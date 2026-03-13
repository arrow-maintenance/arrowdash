#!/usr/bin/env Rscript
# Fetch full details for all PRs (open and closed).
#
# Output: ./data/cache/pr_details.parquet

library(gh)
library(dplyr)
library(purrr)
library(arrow)

output_file <- "./data/cache/pr_details.parquet"

message("=== Fetching all PRs ===")

fetch_prs <- function(state) {
  items <- list()
  page <- 1

  repeat {
    message("Fetching ", state, " page ", page, " ...")

    resp <- gh(
      "GET /repos/{owner}/{repo}/pulls",
      owner = "apache",
      repo = "arrow",
      state = state,
      per_page = 100,
      page = page
    )

    if (length(resp) == 0) break

    items <- c(items, resp)
    message("  Got ", length(resp), " items (total: ", length(items), ")")

    page <- page + 1
    Sys.sleep(0.5)
  }

  items
}

# Fetch both open and closed
open_items <- fetch_prs("open")
closed_items <- fetch_prs("closed")
items <- c(open_items, closed_items)

message("\nConverting to table...")

prs_tbl <- tibble(
  number = map_int(items, "number"),
  title = map_chr(items, "title"),
  state = map_chr(items, "state"),
  draft = map_lgl(items, "draft"),
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
  closed_at = as.POSIXct(
    map_chr(items, ~ .x$closed_at %||% NA_character_),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  merged_at = as.POSIXct(
    map_chr(items, ~ .x$merged_at %||% NA_character_),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  user_login = map_chr(items, list("user", "login")),
  author_association = map_chr(items, "author_association"),
  body = map_chr(items, ~ .x$body %||% NA_character_),
  labels = map(items, ~ map_chr(.x$labels, "name")),
  assignees = map(items, ~ map_chr(.x$assignees, "login")),
  html_url = map_chr(items, "html_url"),
  head_ref = map_chr(items, list("head", "ref")),
  base_ref = map_chr(items, list("base", "ref"))
)

message("\n=== Summary ===")
message("Total PRs: ", nrow(prs_tbl))
message("Open: ", sum(prs_tbl$state == "open"))
message("Closed: ", sum(prs_tbl$state == "closed"))
message("Merged: ", sum(!is.na(prs_tbl$merged_at)))

write_parquet(prs_tbl, output_file)
message("\nSaved to: ", output_file)
