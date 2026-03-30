#!/usr/bin/env Rscript
# Fetch full details for all issues (open and closed), in monthly batches
# using the search API with created: date range.
#
# Progress is saved after each monthly batch to a temp file so the script
# can be resumed if interrupted.
#
# Output: ./data/cache/issue_details.parquet

library(gh)
library(dplyr)
library(purrr)
library(arrow)

output_file <- "./data/cache/issue_details.parquet"
progress_file <- "./data/cache/issue_details_progress.rds"

message("=== Fetching all issues (open + closed) ===")

fetch_issues_for_window <- function(start_date, end_date) {
  # Use search API with created: range
  query <- sprintf(
    "repo:apache/arrow is:issue created:%s..%s",
    start_date,
    end_date
  )
  items <- list()
  page <- 1

  repeat {
    resp <- gh(
      "GET /search/issues",
      q = query,
      per_page = 100,
      page = page
    )

    if (length(resp$items) == 0) {
      break
    }

    items <- c(items, resp$items)
    message("    Page ", page, ": ", length(resp$items), " items")

    # Search API has 1000 result limit
    if (length(items) >= resp$total_count || length(items) >= 1000) {
      break
    }

    page <- page + 1
    Sys.sleep(2.5) # Search API rate limit: 30 req/min
  }

  items
}

# Generate monthly windows from 2023-01-01 to today
start_date <- as.Date("2023-01-01")
end_date <- Sys.Date()
breaks <- seq(start_date, end_date, by = "month")
if (tail(breaks, 1) < end_date) {
  breaks <- c(breaks, end_date)
}

# Load progress if resuming
if (file.exists(progress_file)) {
  progress <- readRDS(progress_file)
  all_items <- progress$all_items
  done_windows <- progress$done_windows
  message(
    "Resuming from saved progress: ",
    length(all_items),
    " issues already fetched, ",
    length(done_windows),
    " windows completed."
  )
} else {
  all_items <- list()
  done_windows <- character(0)
}

for (i in seq_len(length(breaks) - 1)) {
  window_start <- breaks[i]
  window_end <- breaks[i + 1] - 1 # -1 to avoid overlap
  window_key <- paste0(window_start, "/", window_end)

  if (window_key %in% done_windows) {
    message("Skipping (already fetched): ", window_start, " to ", window_end)
    next
  }

  message("Window: ", window_start, " to ", window_end, " ...")
  batch <- fetch_issues_for_window(window_start, window_end)
  all_items <- c(all_items, batch)
  done_windows <- c(done_windows, window_key)
  message("  Got ", length(batch), " | Running total: ", length(all_items))

  # Save progress after every batch
  saveRDS(
    list(all_items = all_items, done_windows = done_windows),
    progress_file
  )

  Sys.sleep(2) # Extra pause between windows
}

# Deduplicate by number
all_items <- all_items[!duplicated(map_int(all_items, "number"))]

message("\nConverting ", length(all_items), " issues to table...")

issues_tbl <- tibble(
  number = map_int(all_items, "number"),
  title = map_chr(all_items, "title"),
  state = map_chr(all_items, "state"),
  created_at = as.POSIXct(
    map_chr(all_items, "created_at"),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  updated_at = as.POSIXct(
    map_chr(all_items, "updated_at"),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  closed_at = as.POSIXct(
    map_chr(all_items, ~ .x$closed_at %||% NA_character_),
    format = "%Y-%m-%dT%H:%M:%SZ",
    tz = "UTC"
  ),
  user_login = map_chr(all_items, list("user", "login")),
  body = map_chr(all_items, ~ .x$body %||% NA_character_),
  labels = map(all_items, ~ map_chr(.x$labels, "name")),
  assignees = map(all_items, ~ map_chr(.x$assignees, "login")),
  html_url = map_chr(all_items, "html_url")
)

message("\n=== Summary ===")
message("Total issues: ", nrow(issues_tbl))
message("  Open:   ", sum(issues_tbl$state == "open"))
message("  Closed: ", sum(issues_tbl$state == "closed"))

write_parquet(issues_tbl, output_file)
message("\nSaved to: ", output_file)

# Clean up progress file on success
if (file.exists(progress_file)) {
  file.remove(progress_file)
  message("Progress file cleaned up.")
}
