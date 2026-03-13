#!/usr/bin/env Rscript
# Fetch all issues and PRs updated since last update, and refresh all cache files.
#
# Updates:
#   - ./data/cache/pr_details.parquet (all PRs)
#   - ./data/cache/issue_details.parquet
#   - ./data/cache/contributors.parquet (first_contribution)

library(gh)
library(dplyr)
library(purrr)
library(arrow)

message("=== Fetching recent activity ===")

# Load existing data to find last update time
prs <- read_parquet("./data/cache/pr_details.parquet")
issues <- read_parquet("./data/cache/issue_details.parquet")

last_update <- max(
  max(prs$updated_at, na.rm = TRUE),
  max(issues$updated_at, na.rm = TRUE)
)

message("Last update: ", last_update)

# Fetch all items updated since then
since_str <- format(last_update, "%Y-%m-%dT%H:%M:%SZ")

items <- list()
page <- 1

repeat {
  message("Fetching page ", page, " ...")

  resp <- gh(
    "GET /repos/{owner}/{repo}/issues",
    owner = "apache",
    repo = "arrow",
    state = "all",
    since = since_str,
    per_page = 100,
    page = page
  )

  if (length(resp) == 0) break

  items <- c(items, resp)
  message("  Got ", length(resp), " items (total: ", length(items), ")")

  page <- page + 1
  Sys.sleep(0.5)
}

message("\nProcessing ", length(items), " updated items...")

# Separate PRs and issues
is_pr <- map_lgl(items, ~ !is.null(.x$pull_request))
updated_issues_raw <- items[!is_pr]
updated_prs_numbers <- map_int(items[is_pr], "number")

# For PRs, we need to fetch from /pulls endpoint to get full PR details
updated_prs_raw <- list()
if (length(updated_prs_numbers) > 0) {
  message("Fetching full PR details for ", length(updated_prs_numbers), " PRs...")
  for (pr_num in updated_prs_numbers) {
    resp <- gh(
      "GET /repos/{owner}/{repo}/pulls/{pull_number}",
      owner = "apache",
      repo = "arrow",
      pull_number = pr_num
    )
    updated_prs_raw <- c(updated_prs_raw, list(resp))
    Sys.sleep(0.2)
  }
}

# Convert updated issues to tibble
if (length(updated_issues_raw) > 0) {
  updated_issues <- tibble(
    number = map_int(updated_issues_raw, "number"),
    title = map_chr(updated_issues_raw, "title"),
    state = map_chr(updated_issues_raw, "state"),
    created_at = as.POSIXct(
      map_chr(updated_issues_raw, "created_at"),
      format = "%Y-%m-%dT%H:%M:%SZ",
      tz = "UTC"
    ),
    updated_at = as.POSIXct(
      map_chr(updated_issues_raw, "updated_at"),
      format = "%Y-%m-%dT%H:%M:%SZ",
      tz = "UTC"
    ),
    user_login = map_chr(updated_issues_raw, list("user", "login")),
    body = map_chr(updated_issues_raw, ~ .x$body %||% NA_character_),
    labels = map(updated_issues_raw, ~ map_chr(.x$labels, "name")),
    assignees = map(updated_issues_raw, ~ map_chr(.x$assignees, "login")),
    html_url = map_chr(updated_issues_raw, "html_url")
  )

  # Update issues - remove old versions, add updated
  # Convert list columns to plain lists for compatibility
  issues <- issues |>
    mutate(
      labels = as.list(labels),
      assignees = as.list(assignees)
    ) |>
    filter(!number %in% updated_issues$number) |>
    bind_rows(updated_issues |> filter(state == "open"))

  write_parquet(issues, "./data/cache/issue_details.parquet")
  message("Updated issue_details.parquet")
}

# Convert updated PRs to tibble
if (length(updated_prs_raw) > 0) {
  updated_prs <- tibble(
    number = map_int(updated_prs_raw, "number"),
    title = map_chr(updated_prs_raw, "title"),
    state = map_chr(updated_prs_raw, "state"),
    draft = map_lgl(updated_prs_raw, "draft"),
    created_at = as.POSIXct(
      map_chr(updated_prs_raw, "created_at"),
      format = "%Y-%m-%dT%H:%M:%SZ",
      tz = "UTC"
    ),
    updated_at = as.POSIXct(
      map_chr(updated_prs_raw, "updated_at"),
      format = "%Y-%m-%dT%H:%M:%SZ",
      tz = "UTC"
    ),
    closed_at = as.POSIXct(
      map_chr(updated_prs_raw, ~ .x$closed_at %||% NA_character_),
      format = "%Y-%m-%dT%H:%M:%SZ",
      tz = "UTC"
    ),
    merged_at = as.POSIXct(
      map_chr(updated_prs_raw, ~ .x$merged_at %||% NA_character_),
      format = "%Y-%m-%dT%H:%M:%SZ",
      tz = "UTC"
    ),
    user_login = map_chr(updated_prs_raw, list("user", "login")),
    author_association = map_chr(updated_prs_raw, "author_association"),
    body = map_chr(updated_prs_raw, ~ .x$body %||% NA_character_),
    labels = map(updated_prs_raw, ~ map_chr(.x$labels, "name")),
    assignees = map(updated_prs_raw, ~ map_chr(.x$assignees, "login")),
    html_url = map_chr(updated_prs_raw, "html_url"),
    head_ref = map_chr(updated_prs_raw, list("head", "ref")),
    base_ref = map_chr(updated_prs_raw, list("base", "ref"))
  )

  # Update PRs - remove old versions, add updated ones
  # Convert list columns to plain lists for compatibility
  prs <- prs |>
    mutate(
      labels = as.list(labels),
      assignees = as.list(assignees)
    ) |>
    filter(!number %in% updated_prs$number) |>
    bind_rows(updated_prs)

  write_parquet(prs, "./data/cache/pr_details.parquet")
  message("Updated pr_details.parquet")
}

# Update first contributions for any new contributors
message("\nUpdating first contributions...")
source("scripts/gh_cache/update_first_contributions.R")

message("\n=== Done ===")
