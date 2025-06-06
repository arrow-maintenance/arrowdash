library(gh)
library(tibble)
library(readr)
library(lubridate)

# Fetch counts
open_issues <- gh("/search/issues", q = "repo:apache/arrow is:issue state:open", .token = Sys.getenv("GITHUB_PAT"))$total_count
open_prs    <- gh("/search/issues", q = "repo:apache/arrow is:pr state:open",    .token = Sys.getenv("GITHUB_PAT"))$total_count

# Record
row <- tibble(
  date = Sys.Date(),
  open_issues = open_issues,
  open_prs = open_prs
)

# Write
csv_path <- "data/open_counts.csv"
dir.create(dirname(csv_path), showWarnings = FALSE, recursive = TRUE)

if (file.exists(csv_path)) {
  existing <- read_csv(csv_path, col_types = cols(date = col_date()))
  if (any(existing$date == row$date)) {
    message("Already recorded today.")
  } else {
    write_csv(row, csv_path, append = TRUE)
    message("Appended new row.")
  }
} else {
  write_csv(row, csv_path)
  message("Created file and wrote first row.")
}