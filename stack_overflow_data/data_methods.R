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
library(gt)
library(httr)
library(lubridate)
library(tidyr)

get_data <- function(api_name, url){

  api_data <- httr::GET(url)
  out <- content(api_data, as = "text") %>%
    jsonlite::fromJSON()

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

get_comments <- function(question_ids){

  comments_content <- get_data(
    api_name = "comments",
    url = paste0(
      "https://api.stackexchange.com/2.3/questions/",
      paste(question_ids, collapse = ";"),
      "/comments?order=desc&sort=creation&site=stackoverflow&filter=!-).qJXDT0Z5I"
    )
  )

  if (nrow(comments_content$items) == 0) {
    return(NULL)
  }

  comments_content$items %>%
    tidyr::unnest(owner) %>%
    select(display_name, account_id, score, post_id, comment_id, creation_date)

}

get_answers <- function(question_ids){

  answers_content <- get_data(
    api_name = "answers",
    url = paste0(
      "https://api.stackexchange.com/2.3/questions/",
      paste(question_ids, collapse = ";"),
      "/answers?order=desc&sort=activity&site=stackoverflow&filter=!9Rgp29w2U"
    )
  )

  if (nrow(answers_content$items) == 0) {
    return(NULL)
  }

  answers_content$items %>%
    tidyr::unnest(owner) %>%
    select(display_name, account_id, score, is_accepted, question_id, creation_date)
}

adjust_data <- function(questions_content){

  questions <- questions_content$items %>%
    mutate(last_activity_date = as_datetime(last_activity_date)) %>%
    mutate(retrieved = now())

  # retrieve comments
  comments <- get_comments(questions$question_id)

  # get counts of comments
  reply_counts <- comments %>%
    select(question_id = post_id) %>%
    group_by(question_id) %>%
    summarise(comments = n())

  answers <- get_answers(questions$question_id)
  answer_counts <- answers %>%
    select(question_id) %>%
    group_by(question_id) %>%
    summarise(answers = n())

  answer_accepted <- answers %>%
    filter(is_accepted) %>%
    select(question_id, is_accepted)

  # add in raw data, reply counts, and whether an answer has been accepted
  left_join(questions, reply_counts, by = "question_id") %>%
    left_join(answer_counts, by = "question_id") %>%
    left_join(answer_accepted, by = "question_id") %>%
    replace_na(list(is_accepted = FALSE, comments = 0, answers = 0)) %>%
      select(link, title, last_activity_date, comments, answers, accepted_answer = is_accepted) %>%
      mutate(days_since_last_activity = round(as.numeric(as.duration(interval(last_activity_date, now())), "days"))) %>%
      mutate(issue = paste0('<a href="',link,'" target="_blank">', title , '</a>'))
}

gt_show_questions <- function(data_adjusted){
  display_data <- data_adjusted %>%
    mutate(Question = paste0("[", title, "](", link, ")")) %>%
    select(Question, Answers = answers, `Accepted?` = accepted_answer,
           Comments = comments, `Days since activity` = days_since_last_activity)

  no_answer_rows <- which(!data_adjusted$accepted_answer)

  tbl <- display_data %>%
    gt() %>%
    fmt_markdown(columns = Question) %>%
    cols_width(
      Question ~ pct(50),
      Answers ~ pct(12),
      `Accepted?` ~ pct(12),
      Comments ~ pct(12),
      `Days since activity` ~ pct(14)
    ) %>%
    tab_options(
      table.width = pct(100),
      container.height = px(400),
      container.overflow.y = TRUE
    )

  if (length(no_answer_rows) > 0) {
    tbl <- tbl %>%
      tab_style(
        style = cell_fill(color = "#fbcd9989"),
        locations = cells_body(rows = no_answer_rows)
      )
  }

  tbl
}
