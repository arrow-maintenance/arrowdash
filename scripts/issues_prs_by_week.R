library(gh)
library(lubridate)
library(dplyr)

fetch_weekly_counts <- function(type = "issue", start_date = NULL, end_date = NULL, state = "created") {
  if (!type %in% c("issue", "pr")) stop("type must be 'issue' or 'pr'")
  if (!state %in% c("created", "closed")) stop("state must be 'created' or 'closed'")
  
  if (is.null(start_date)) start_date <- Sys.Date() - 7
  if (is.null(end_date)) end_date <- Sys.Date()
  
  current <- start_date
  results <- list()
  
  while (current < end_date) {
    next_week <- current + 7
    date_range <- paste0(current, "..", next_week)
    query <- sprintf("repo:apache/arrow is:%s %s:%s", type, state, date_range)
    
    resp <- gh("/search/issues", q = query)
    total_count <- resp$total_count
    
    results[[length(results) + 1]] <- tibble(
      week_start = as.Date(current),
      n = total_count
    )
    
    Sys.sleep(2.1)  # GitHub rate limit safety buffer
    current <- next_week
  }
  
  bind_rows(results)
}

get_last_sunday <- function(today = Sys.Date()) {
  weekday <- wday(today) %% 7  # make Sunday = 0
  today - days(weekday)
}


update_items_csv <- function(type = "issue", state = "created", csv_path = "./data/issues_opened.csv") {
  if (file.exists(csv_path)) {
    existing_data <- read_csv(
      csv_path,
      col_types = cols(
        week_start = col_date(),
        n = col_integer()
      )
    )
    
  } else {
    existing_data <- tibble(week_start = character(), n = integer())
  }
  
  if (nrow(existing_data) > 0) {
    last_week <- max(as.Date(existing_data$week_start))
  } else {
    last_week <- get_last_sunday() - weeks(208)
  }
  
  next_week <- last_week + 7
  this_sunday <- get_last_sunday()
  
  if (next_week >= this_sunday) {
    message(sprintf("%s data is already up to date.", tools::toTitleCase(state)))
    return(invisible())
  }
  
  message(sprintf("Fetching %s %s data from %s to %s", state, type, next_week, this_sunday))
  new_data <- fetch_weekly_counts(type, next_week, this_sunday, state)
  all_data <- bind_rows(existing_data, new_data) %>%
    arrange(as.Date(week_start))
  
  dir.create(dirname(csv_path), showWarnings = FALSE, recursive = TRUE)
  write_csv(all_data, csv_path)
  
  message(sprintf("Updated %s with %d new rows.", csv_path, nrow(new_data)))
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
  csv_path = "./data/pr_opened.csv"
)

update_items_csv(
  type = "pr",
  state = "closed",
  csv_path = "./data/pr_closed.csv"
)
