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
library(glue)
library(httr)
library(lubridate)

dt_show_issues <- function(x){

  display_data <- x %>%
    mutate(new_contributor = author_association %in% c("NONE", "FIRST_TIME_CONTRIBUTOR")) %>%
    select(created_at, url_title, html_url, new_contributor)

  selected_rows <- which(display_data$new_contributor == TRUE)
  DT::datatable(
    select(display_data, -new_contributor),
    escape = FALSE,
    extensions = 'Buttons',
    options = list(
      dom = 'Bfrtip',
      buttons = c('copy', 'csv', 'excel'),
      pageLength = 10
    )
  ) %>%
    formatDate("created_at", method = "toUTCString") %>%
    formatStyle("created_at", target = "row", backgroundColor = styleRow(selected_rows, 'lightblue'))
}

get_data <- function(api_name, url){
  # message("retrieving ", api_name, " data from Stack Exchange API")

  api_data <- httr::GET(url)

  # if (api_data$status_code == 200) {
  #   message(api_name, " data successfully retrieved")
  # } else {
  #   warning("status code ", api_data$status_code, " when querying", api_name, "API")
  # }

  out <- content(api_data, as = "text") %>%
    jsonlite::fromJSON()

  # message(nrow(out$items) %||% 0, " items retrieved")

  out

}

#' Get questions from Stack Overflow containing the specified tags
#'
#' @param tags Character vector of tags
#' @examples
#' get_questions(c("apache-arrow", "r"))
#' get_questions(c("apache-arrow", "python"))
#' get_questions("pyarrow")
#'
get_questions <- function(tags){

  tag_string <- paste(tags, collapse = "%3B")
  url <- glue("https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged={tag_string}&site=stackoverflow&filter=!-nt6H9OZ4WW*msaSa)YvngdWhKQ).R9VfXkayFbhnB61(g5UUJbH7f")

  out <- get_data(
    api_name = "questions",
    url = url
  )

  out
}

get_raw_data <- function(questions_content){

  # reformat date columns
  questions <- questions_content$items %>%
    mutate(last_activity_date = as_datetime(last_activity_date)) %>%
    mutate(retrieved = now())
}

dt_show_questions <- function(row_data){

  so_data_adjusted <- so_data %>%
  select(link, title, last_activity_date) %>%
  mutate(days_since_last_activity = round(as.numeric(as.duration(interval(last_activity_date, now())), "days"))) %>%
  select(-last_activity_date)

  DT::datatable(
    escape = FALSE,
    so_data_adjusted %>%
      mutate(issue = paste0("<a href='",link,"' target='_blank'>", title , "</a>")) %>%
      select(issue, everything(), -link, -title)
  )
}
