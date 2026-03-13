#!/usr/bin/env Rscript
# Fetch full details for all open issues.
#
# Output: ./data/cache/issue_details.parquet

library(gh)
library(dplyr)
library(purrr)
library(arrow)

output_file <- "./data/cache/issue_details.parquet"

message("=== Fetching all open issues ===")

items <- list()
page <- 1

repeat {
  message("Fetching page ", page, " ...")

  resp <- gh(
    "GET /repos/{owner}/{repo}/issues",
    owner = "apache",
    repo = "arrow",
    state = "open",
    per_page = 100,
    page = page
  )

  if (length(resp) == 0) {
    break
  }

  # Filter out PRs (issues endpoint includes PRs)
  issues_only <- keep(resp, ~ is.null(.x$pull_request))
  items <- c(items, issues_only)
  message("  Got ", length(issues_only), " issues (total: ", length(items), ")")

  page <- page + 1
  Sys.sleep(0.5)
}

message("\nConverting to table...")

issues_tbl <- tibble(
  number = map_int(items, "number"),
  title = map_chr(items, "title"),
  state = map_chr(items, "state"),
  created_at = as.POSIXct(
    map_chr(items, "created_at"),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  updated_at = as.POSIXct(
    map_chr(items, "updated_at"),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  user_login = map_chr(items, list("user", "login")),
  body = map_chr(items, ~ .x$body %||% NA_character_),
  labels = map(items, ~ map_chr(.x$labels, "name")),
  assignees = map(items, ~ map_chr(.x$assignees, "login")),
  html_url = map_chr(items, "html_url")
)

message("\n=== Summary ===")
message("Total open issues: ", nrow(issues_tbl))

write_parquet(issues_tbl, output_file)
message("\nSaved to: ", output_file)
