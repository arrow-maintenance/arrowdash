# MIT license

# Copyright (c) 2024 ???

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

library(DT)
library(dplyr)
library(gt)
library(glue)
library(readr)
library(arrow)
library(lubridate)

# CSV data reading helpers for decoupled Python/R architecture

read_first_merged_dates <- function() {
  arrow::read_parquet("data/cache/pr_details.parquet") %>%
    filter(
      !grepl("\\[bot\\]", user_login, ignore.case = TRUE),
      !is.na(merged_at)
    ) %>%
    group_by(user_login) %>%
    summarise(first_merged_at = min(merged_at), .groups = "drop")
}

# Read open issues/PRs from parquet cache, filtered by language label and last 3 months
read_open_issues <- function(lang) {
  label <- paste0("Component: ", lang)
  cutoff <- Sys.time() - months(3)
  issues <- arrow::read_parquet("data/cache/issue_details.parquet")
  first_merged <- read_first_merged_dates()

  issues %>%
    filter(created_at > cutoff) %>%
    filter(purrr::map_lgl(labels, ~ label %in% .x)) %>%
    left_join(first_merged, by = "user_login") %>%
    mutate(
      new_contributor = is.na(first_merged_at) | created_at < first_merged_at
    ) %>%
    transmute(
      created_at = created_at,
      url_title = paste0('<a target="_blank" href="', html_url, '">', title, '</a>'),
      html_url = html_url,
      new_contributor = new_contributor,
      comments = 0L
    ) %>%
    arrange(desc(created_at))
}

read_open_prs <- function(lang) {
  label <- paste0("Component: ", lang)
  cutoff <- Sys.time() - months(3)
  prs <- arrow::read_parquet("data/cache/pr_details.parquet")
  first_merged <- read_first_merged_dates()

  prs %>%
    filter(state == "open") %>%
    filter(created_at > cutoff) %>%
    filter(purrr::map_lgl(labels, ~ label %in% .x)) %>%
    left_join(first_merged, by = "user_login") %>%
    mutate(
      new_contributor = is.na(first_merged_at) | created_at < first_merged_at
    ) %>%
    transmute(
      created_at = created_at,
      url_title = paste0('<a target="_blank" href="', html_url, '">', title, '</a>'),
      html_url = html_url,
      new_contributor = new_contributor,
      comments = 0L
    ) %>%
    arrange(desc(created_at))
}

read_ml_summary <- function() {
  readLines("data/dev_ml_summary.txt", warn = FALSE) |> paste(collapse = "\n")
}

gt_show_issues <- function(x){

  display_data <- x %>%
    mutate(
      Title = url_title,
      Date = as.Date(created_at)
    ) %>%
    select(Date, Title, new_contributor)

  tbl <- display_data %>%
    select(-new_contributor) %>%
    gt() %>%
    fmt_markdown(columns = Title) %>%
    fmt_date(columns = Date, date_style = "iso") %>%
    cols_width(
      Date ~ pct(15),
      Title ~ pct(85)
    ) %>%
    tab_options(
      table.width = pct(100),
      container.height = px(400),
      container.overflow.y = TRUE
    )

  # Highlight new contributor rows
  new_contrib_rows <- which(display_data$new_contributor)
  if (length(new_contrib_rows) > 0) {
    tbl <- tbl %>%
      tab_style(
        style = cell_fill(color = "#fbcd9989"),
        locations = cells_body(rows = new_contrib_rows)
      )
  }

  tbl
}
