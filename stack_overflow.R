library(httr)
library(dplyr)
library(lubridate)
library(tidyr)
library(DT)
library(rlang)
library(glue)

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

get_so_comments <- function(question_ids){

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
  # here's the table of comments! we can count them
  comments_content$items %>%
    tidyr::unnest(owner) %>%
    select(display_name, account_id, score, post_id, comment_id, creation_date)

}

get_so_answers <- function(question_ids){

  answers_content <- get_data(
    api_name = "answers",
    url = paste0(
      "https://api.stackexchange.com/2.3/questions/",
      paste(question_ids, collapse = ";"),
      "/answers?order=desc&sort=activity&site=stackoverflow&filter=!9Rgp29w2U"
    )
  )

  # here's the table of comments! we can count them
  answers_content$items %>%
    tidyr::unnest(owner) %>%
    select(display_name, account_id, score, is_accepted, question_id, creation_date)
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

get_raw_so_data <- function(){

  questions_content <- get_questions(c("apache-arrow", "r")) %>%
    bind_rows(get_questions(c("apache-arrow", "python"))) %>%
    bind_rows(get_questions(c("pyarrow")))

  # reformat date columns
  questions <- questions_content$items %>%
    mutate(last_activity_date = as_datetime(last_activity_date)) %>%
    mutate(retrieved = now())

  # retrieve comments
  comments <- get_so_comments(questions$question_id)

  # get counts of comments
  reply_counts <- comments %>%
    select(question_id = post_id) %>%
    group_by(question_id) %>%
    summarise(comments = n())

  answers <- get_so_answers(questions$question_id)
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
    replace_na(list(is_accepted = FALSE, comments = 0, answers = 0))
}



so_data <- get_raw_so_data()
last_date_retrieved <- so_data %>% slice(1) %>% pull(retrieved)

so_data_adjusted <- so_data %>%
  select(link, title, last_activity_date, comments, answers, accepted_answer = is_accepted) %>%
  mutate(days_since_last_activity = round(as.numeric(as.duration(interval(last_activity_date, now())), "days"))) %>%
  select(-last_activity_date)

# To output to CSV
readr::write_csv(so_data_adjusted, "so_data.csv")

# To output to datatable
DT::datatable(
  escape = FALSE,
  so_data_adjusted %>%
    mutate(issue = paste0("<a href='",link,"' target='_blank'>", title , "</a>")) %>%
    select(issue, everything(), -link, -title)
)
