library(gh)
library(dplyr)
library(lubridate)
library(readr)
library(purrr)
library(tibble)

# Config
owner <- "apache"
repo <- "arrow"

# Ensure data directory exists
dir.create("data", showWarnings = FALSE, recursive = TRUE)

message("=== Starting consolidated data update ===")

# ==============================================================================
# 1. DAILY: Update open issue/PR counts
# ==============================================================================
message("1. Updating daily open counts...")

update_open_counts <- function() {
  # Simple search API calls for current open counts
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
  
  if (file.exists(csv_path)) {
    existing <- read_csv(csv_path, col_types = cols(date = col_date()))
    if (any(existing$date == row$date)) {
      message("  → Open counts already recorded for today")
    } else {
      write_csv(row, csv_path, append = TRUE)
      message(paste("  → Recorded:", row$open_issues, "issues,", row$open_prs, "PRs"))
    }
  } else {
    write_csv(row, csv_path)
    message(paste("  → Created file with:", row$open_issues, "issues,", row$open_prs, "PRs"))
  }
}

update_open_counts()

# ==============================================================================
# 2. DAILY: Update current month commit count (running total)
# ==============================================================================
message("2. Updating monthly commit counts...")

update_monthly_commits <- function() {
  current_month <- format(Sys.Date(), "%Y-%m")
  month_start <- floor_date(Sys.Date(), "month")
  commit_file <- "./data/monthly_commit_counts.csv"
  
  # Load existing data
  if (file.exists(commit_file)) {
    existing_data <- read_csv(commit_file, col_types = cols(
      month = col_character(),
      commit_count = col_integer()
    ))
  } else {
    existing_data <- tibble(month = character(), commit_count = integer())
  }
  
  # Get commit count for current month (from start of month to now)
  commits <- gh(
    "/repos/:owner/:repo/commits",
    owner = owner,
    repo = repo,
    since = paste0(month_start, "T00:00:00Z"),
    until = paste0(Sys.Date() + 1, "T00:00:00Z"),
    .limit = Inf
  )
  
  current_month_commits <- length(commits)
  
  # Update or add current month data
  if (current_month %in% existing_data$month) {
    # Update existing current month row
    existing_data$commit_count[existing_data$month == current_month] <- current_month_commits
    message(paste("  → Updated", current_month, "with", current_month_commits, "commits (running total)"))
  } else {
    # Add new row for current month
    new_row <- tibble(
      month = current_month,
      commit_count = current_month_commits
    )
    existing_data <- bind_rows(existing_data, new_row)
    message(paste("  → Added", current_month, "with", current_month_commits, "commits (running total)"))
  }
  
  # Write updated data
  write_csv(existing_data, commit_file)
}

update_monthly_commits()

# Also update completed months if needed (monthly logic from original script)
update_completed_months <- function() {
  commit_file <- "./data/monthly_commit_counts.csv"
  existing_data <- read_csv(commit_file, col_types = cols(
    month = col_character(),
    commit_count = col_integer()
  ))
  
  # Only process complete months
  end_date <- floor_date(Sys.Date(), "month") - days(1)  # Last complete month
  
  # Determine where to start
  last_month <- max(existing_data$month[existing_data$month != format(Sys.Date(), "%Y-%m")])
  if (length(last_month) == 0 || is.na(last_month)) {
    # Start from a reasonable date if no data
    start_date <- as.Date("2024-01-01")
  } else {
    start_date <- as.Date(paste0(last_month, "-01")) %m+% months(1)
  }
  
  # Early exit if up to date
  if (start_date > end_date) {
    message("  → Complete months already up to date")
    return()
  }
  
  # Generate list of months to process
  months <- seq.Date(start_date, end_date, by = "month")
  
  if (length(months) > 0) {
    message(paste("  → Updating", length(months), "complete months"))
    
    # GitHub API query for completed months
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
    
    # Build new data for completed months
    new_data <- map2_df(
      months,
      months + months(1) - 1,
      ~ tibble(
        month = format(.x, "%Y-%m"),
        commit_count = get_commit_count(.x, .y)
      )
    )
    
    # Update existing data (remove current month entries that might be incomplete)
    existing_data <- existing_data[!existing_data$month %in% new_data$month, ]
    updated_data <- bind_rows(existing_data, new_data)
    write_csv(updated_data, commit_file)
    message("  → Updated completed months")
  }
}

# Run monthly completion update (this handles historical months)
update_completed_months()

# ==============================================================================
# 3. DAILY: Update daily issue/PR activity counts
# ==============================================================================
message("3. Updating daily issue/PR activity counts...")

update_daily_activity <- function() {
  today <- Sys.Date()
  yesterday <- today - 1
  
  # Helper function to get count for a specific day
  get_daily_count <- function(type, state, date) {
    query <- sprintf("repo:apache/arrow is:%s %s:%s", type, state, format(date, "%Y-%m-%d"))
    resp <- gh("/search/issues", q = query, .token = Sys.getenv("GH_API_TOKEN"))
    resp$total_count
  }
  
  # Helper function to update a daily CSV file
  update_daily_csv <- function(type, state, csv_path) {
    # Load existing data
    if (file.exists(csv_path)) {
      existing_data <- read_csv(csv_path, col_types = cols(date = col_date(), n = col_integer()))
      last_date <- max(existing_data$date)
    } else {
      existing_data <- tibble(date = as.Date(character()), n = integer())
      last_date <- today - days(30) # Start from 30 days ago if no data
    }
    
    # Determine dates to update (from day after last_date to yesterday)
    start_date <- last_date + 1
    
    if (start_date > yesterday) {
      message(sprintf("    → %s %s data is up to date", tools::toTitleCase(state), type))
      return()
    }
    
    message(sprintf("    → Updating %s %s from %s to %s", state, type, start_date, yesterday))
    
    # Get data for each missing day
    dates_to_update <- seq.Date(start_date, yesterday, by = "day")
    
    for (date in dates_to_update) {
      count <- get_daily_count(type, state, as.Date(date, origin = "1970-01-01"))
      new_row <- tibble(date = as.Date(date, origin = "1970-01-01"), n = count)
      
      existing_data <- bind_rows(existing_data, new_row)
      message(sprintf("      → %s: %d", as.Date(date, origin = "1970-01-01"), count))
      
      # Rate limiting protection (30 requests/minute)
      Sys.sleep(2.1)
    }
    
    # Write updated data
    write_csv(existing_data, csv_path)
  }
  
  # Update all daily activity files
  update_daily_csv("issue", "created", "./data/issues_opened_daily.csv")
  update_daily_csv("issue", "closed", "./data/issues_closed_daily.csv")
  update_daily_csv("pr", "created", "./data/prs_opened_daily.csv")
  update_daily_csv("pr", "closed", "./data/prs_closed_daily.csv")
}

update_daily_activity()

message("=== Consolidated data update complete ===")