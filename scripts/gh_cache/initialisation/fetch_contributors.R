#!/usr/bin/env Rscript
# Fetch all contributors from the Apache Arrow repo.
#
# Output: ./data/cache/contributors.parquet

library(gh)
library(dplyr)
library(purrr)
library(arrow)

output_file <- "./data/cache/contributors.parquet"

message("=== Fetching contributors ===")

items <- list()
page <- 1

repeat {
  message("Fetching page ", page, " ...")

  resp <- gh(
    "GET /repos/{owner}/{repo}/contributors",
    owner = "apache",
    repo = "arrow",
    per_page = 100,
    page = page
  )

  if (length(resp) == 0) {
    break
  }

  items <- c(items, resp)
  message("  Got ", length(resp), " contributors (total: ", length(items), ")")

  page <- page + 1
  Sys.sleep(0.5)
}

message("\nConverting to table...")

contributors_tbl <- tibble(
  login = map_chr(items, "login"),
  id = map_int(items, "id"),
  type = map_chr(items, "type"),
  contributions = map_int(items, "contributions"),
  html_url = map_chr(items, "html_url"),
  avatar_url = map_chr(items, "avatar_url"),
  site_admin = map_lgl(items, "site_admin"),
  first_pr = NA_integer_
)

message("\n=== Summary ===")
message("Total contributors: ", nrow(contributors_tbl))

write_parquet(contributors_tbl, output_file)
message("\nSaved to: ", output_file)
