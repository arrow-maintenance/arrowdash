#!/usr/bin/env Rscript
# Fetch review status for first-time contributor PRs.
# Checks both issue comments AND pull request reviews for human activity.
# Also records last actor and last activity date to identify abandoned PRs.
# Safe to re-run — overwrites first_timer_review_status.csv

library(gh)
library(dplyr)
library(purrr)
library(arrow)

token <- Sys.getenv("GITHUB_PAT")
out_file <- "first_timer_review_status.csv"
cutoff <- as.POSIXct(Sys.Date() - 365, tz = "UTC")

pr_details <- read_parquet("../data/cache/pr_details.parquet")

first_merged_prs <- pr_details |>
  filter(!is.na(merged_at)) |>
  group_by(user_login) |>
  summarise(first_merged_at = min(as.POSIXct(merged_at, tz = "UTC")), .groups = "drop")

first_timer_prs <- pr_details |>
  left_join(first_merged_prs, by = "user_login") |>
  filter(
    is.na(first_merged_at) | as.POSIXct(created_at, tz = "UTC") < first_merged_at,
    as.POSIXct(created_at, tz = "UTC") >= cutoff
  )

message("Checking ", nrow(first_timer_prs), " first-timer PRs...")

bot_pattern <- "\\[bot\\]|github-actions|codecov|dependabot"

fetch_review_status <- function(number, author) {
  # Check issue comments
  issue_comments <- tryCatch(
    gh(
      "GET /repos/{owner}/{repo}/issues/{issue_number}/comments",
      owner = "apache",
      repo = "arrow",
      issue_number = number,
      per_page = 100,
      .token = token
    ),
    error = function(e) list()
  )

  # Check PR reviews
  pr_reviews <- tryCatch(
    gh(
      "GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews",
      owner = "apache",
      repo = "arrow",
      pull_number = number,
      per_page = 100,
      .token = token
    ),
    error = function(e) list()
  )

  # Build unified activity timeline
  activity <- bind_rows(
    map_dfr(issue_comments, function(c) {
      tibble(
        login = c$user$login,
        at = as.POSIXct(c$created_at, format = "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
      )
    }),
    map_dfr(pr_reviews, function(r) {
      tibble(
        login = r$user$login,
        at = as.POSIXct(
          r$submitted_at,
          format = "%Y-%m-%dT%H:%M:%SZ",
          tz = "UTC"
        )
      )
    })
  ) |>
    filter(!grepl(bot_pattern, login, ignore.case = TRUE)) |>
    arrange(at)

  human_activity <- activity |> filter(login != author)

  last_event <- if (nrow(activity) > 0) slice_tail(activity, n = 1) else NULL
  last_human <- if (nrow(human_activity) > 0) {
    slice_tail(human_activity, n = 1)
  } else {
    NULL
  }

  Sys.sleep(0.2)

  tibble(
    number = number,
    author = author,
    has_human_review = nrow(human_activity) > 0,
    n_comments = nrow(activity),
    reviewers = paste(unique(human_activity$login), collapse = ", "),
    last_actor = if (!is.null(last_event)) last_event$login else NA_character_,
    last_activity_at = if (!is.null(last_event)) {
      last_event$at
    } else {
      as.POSIXct(NA)
    },
    last_human_actor = if (!is.null(last_human)) {
      last_human$login
    } else {
      NA_character_
    },
    last_human_at = if (!is.null(last_human)) last_human$at else as.POSIXct(NA),
    awaiting_author = nrow(human_activity) > 0 &&
      !is.null(last_event) &&
      last_event$login != author
  )
}

results <- map2_dfr(
  first_timer_prs$number,
  first_timer_prs$user_login,
  fetch_review_status,
  .progress = TRUE
)

message("\nResults:")
message("  Total PRs:           ", nrow(results))
message("  Has human review:    ", sum(results$has_human_review))
message("  No review:           ", sum(!results$has_human_review))
message("  Awaiting author:     ", sum(results$awaiting_author, na.rm = TRUE))

write.csv(results, out_file, row.names = FALSE)
message("\nSaved to: ", out_file)
