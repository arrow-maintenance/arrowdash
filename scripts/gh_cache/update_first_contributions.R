#!/usr/bin/env Rscript
# Update contributors table with their first PR contribution number.
#
# Reads:
#   - ./data/cache/contributors.parquet
#   - ./data/cache/pr_details.parquet
#
# Updates: ./data/cache/contributors.parquet

library(dplyr)
library(arrow)

message("=== Updating first contributions ===")

# Load data
contributors <- read_parquet("./data/cache/contributors.parquet")
all_prs <- read_parquet("./data/cache/pr_details.parquet") |>
  select(number, user_login, created_at)

# Find first PR per user
first_prs <- all_prs |>
  group_by(user_login) |>
  slice_min(created_at, n = 1, with_ties = FALSE) |>
  ungroup() |>
  select(login = user_login, first_pr = number)

# Find contributors needing update
needs_update <- contributors |>
  filter(is.na(first_pr)) |>
  pull(login)

message("Contributors needing update: ", length(needs_update))

# Update contributors with first contribution
updated_contributors <- contributors |>
  rows_update(
    first_prs |> filter(login %in% needs_update),
    by = "login"
  )

# Summary
found <- sum(!is.na(updated_contributors$first_pr)) - sum(!is.na(contributors$first_pr))
still_missing <- sum(is.na(updated_contributors$first_pr))

message("Updated: ", found)
message("Still missing (commit-only contributors): ", still_missing)

write_parquet(updated_contributors, "./data/cache/contributors.parquet")
message("\nSaved to: ./data/cache/contributors.parquet")
