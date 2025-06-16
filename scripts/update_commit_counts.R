library(gh)
library(dplyr)
library(lubridate)
library(readr)
library(purrr)

# Config
owner <- "apache"
repo <- "arrow"
end_date <- floor_date(Sys.Date(), "month") - days(1)  # Last complete month

# Load existing data
commit_file <- "./data/monthly_commit_count.csv"
existing_data <- read_csv(commit_file, col_types = cols(
  month = col_character(),
  commit_count = col_integer()
))

# Determine where to start
last_month <- max(existing_data$month)
start_date <- as.Date(paste0(last_month, "-01")) %m+% months(1)

# Early exit if up to date
if (start_date > end_date) {
  message("Data already up to date.")
} else {
  # Generate list of months to process
  months <- seq.Date(start_date, end_date, by = "month")
  
  # GitHub API query
  get_commit_count <- function(since, until) {
    commits <- gh(
      "/repos/:owner/:repo/commits",
      owner = owner,
      repo = repo,
      since = paste0(since, "T00:00:00Z"),
      until = paste0((until + 1), "T00:00:00Z"),
      .limit = Inf
    )
    length(commits)
  }
  
  # Build new data
  new_data <- map2_df(
    months,
    months + months(1) - 1,
    ~ tibble(
      month = format(.x, "%Y-%m"),
      commit_count = get_commit_count(.x, .y)
    )
  )
  
  # Append and write
  updated_data <- bind_rows(existing_data, new_data)
  write_csv(updated_data, commit_file)
  message("Appended new data and updated CSV.")
}
