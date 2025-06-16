library(gh)
library(lubridate)
library(dplyr)
library(readr)

fetch_weekly_counts_stream <- function(type, start_date, end_date, state, csv_path) {
  current <- start_date
  first_write <- !file.exists(csv_path)
  
  while (current < end_date) {
    next_week <- current + 7
    date_range <- paste0(current, "..", next_week)
    query <- sprintf("repo:apache/arrow is:%s %s:%s", type, state, date_range)
    
    resp <- gh("/search/issues", q = query, .token = Sys.getenv("GH_API_TOKEN"))
    total_count <- resp$total_count
    
    row <- tibble(week_start = as.Date(current), n = total_count)
    
    # Append row to file
    write_csv(
      row,
      csv_path,
      append = !first_write,
      col_names = first_write
    )
    first_write <- FALSE
    
    message(sprintf("Wrote %s → %d", current, total_count))
    current <- next_week
  }
}

get_last_sunday <- function(today = Sys.Date()) {
  weekday <- as.integer(format(today, "%w"))  # Sunday = 0, Monday = 1, ..., Saturday = 6
  if (weekday == 0) {
    return(today)
  } else {
    return(today - weekday)
  }
}

update_items_csv <- function(type = "issue", state = "created", csv_path = NULL) {
  if (is.null(csv_path)) {
    csv_path <- file.path("data", paste0(type, "s_", state, ".csv"))
  }
  
  if (file.exists(csv_path)) {
    existing_data <- read_csv(csv_path, col_types = cols(week_start = col_date(), n = col_integer()))
    last_week <- max(existing_data$week_start)
  } else {
    existing_data <- tibble()
    last_week <- get_last_sunday() - weeks(208)
  }
  
  next_week <- last_week + 7
  this_sunday <- get_last_sunday()
  
  if (next_week >= this_sunday) {
    message(sprintf("%s data is already up to date.", tools::toTitleCase(state)))
    return(invisible())
  }
  
  message(sprintf("Fetching %s %s data from %s to %s", state, type, next_week, this_sunday))
  dir.create(dirname(csv_path), recursive = TRUE, showWarnings = FALSE)
  
  fetch_weekly_counts_stream(type, next_week, this_sunday, state, csv_path)
}

update_items_csv(
  type = "issue",
  state = "created",
  csv_path = "./data/issues_opened.csv"
)

update_items_csv(
  type = "issue",
  state = "closed",
  csv_path = "./data/issues_closed.csv"
)

update_items_csv(
  type = "pr",
  state = "created",
  csv_path = "./data/prs_opened.csv"
)

update_items_csv(
  type = "pr",
  state = "closed",
  csv_path = "./data/prs_closed.csv"
)
