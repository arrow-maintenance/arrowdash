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

read_all_prs <- function() {
  bind_rows(
    arrow::read_parquet("data/cache/open_prs.parquet"),
    arrow::read_parquet("data/cache/closed_prs.parquet")
  )
}

read_all_issues <- function() {
  bind_rows(
    arrow::read_parquet("data/cache/open_issues.parquet"),
    arrow::read_parquet("data/cache/closed_issues.parquet")
  )
}

read_first_merged_dates <- function() {
  arrow::read_parquet("data/cache/closed_prs.parquet") %>%
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
  issues <- arrow::read_parquet("data/cache/open_issues.parquet")
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
  prs <- arrow::read_parquet("data/cache/open_prs.parquet")
  first_merged <- read_first_merged_dates()

  prs %>%
    filter(!draft) %>%
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

# ---- Bug Backlog page --------------------------------------------------------

# Bugs opened before this date are the ones the backlog clean-up is tracking.
old_bug_cutoff <- as.Date("2026-07-30")

is_bug <- function(labels) {
  purrr::map_lgl(labels, ~ "Type: bug" %in% .x)
}

# "Component: X" labels stripped to "X"; issues with none get "(No component)"
extract_components <- function(labels) {
  lapply(labels, function(x) {
    comps <- sub("^Component: ", "", grep("^Component: ", x, value = TRUE))
    if (length(comps) == 0) "(No component)" else comps
  })
}

# One row per (bug, component). Bugs with several component labels appear once
# per component, so counts across components overshoot the number of bugs.
read_bugs_by_component <- function() {
  read_all_issues() %>%
    filter(is_bug(labels)) %>%
    mutate(component = extract_components(labels)) %>%
    tidyr::unnest(component) %>%
    transmute(
      number,
      component,
      state,
      created = as.Date(created_at),
      closed = as.Date(closed_at)
    )
}

count_open_old_bugs <- function(bugs, cutoff = old_bug_cutoff) {
  bugs %>%
    filter(state == "open", created < cutoff) %>%
    distinct(number) %>%
    nrow()
}

count_old_bugs_closed_since <- function(bugs, since, cutoff = old_bug_cutoff) {
  bugs %>%
    filter(!is.na(closed), closed >= since, created < cutoff) %>%
    distinct(number) %>%
    nrow()
}

open_bugs_by_year <- function(bugs) {
  bugs %>%
    filter(state == "open") %>%
    mutate(year = lubridate::year(created)) %>%
    count(component, year) %>%
    tidyr::pivot_wider(
      names_from = year, values_from = n, values_fill = 0, names_sort = TRUE
    ) %>%
    mutate(Total = rowSums(across(-component))) %>%
    arrange(desc(Total))
}

# GitHub issue search for open bugs in a component, optionally limited to the
# year they were opened. Vectorised over component.
bug_search_url <- function(component, year = NULL) {
  terms <- c('is:issue', 'state:open', 'label:"Type: bug"')
  if (!is.null(year)) {
    terms <- c(terms, sprintf("created:%d-01-01..%d-12-31", year, year))
  }
  queries <- paste(
    paste(terms, collapse = " "),
    sprintf('label:"Component: %s"', component)
  )
  paste0(
    "https://github.com/apache/arrow/issues?q=",
    vapply(queries, utils::URLencode, character(1), reserved = TRUE, USE.NAMES = FALSE)
  )
}

# Wrap non-empty cell text in an unstyled link; cells with no URL are left alone
link_cells <- function(urls) {
  force(urls)
  function(x) {
    ifelse(
      x == "" | is.na(urls),
      x,
      sprintf(
        '<a href="%s" target="_blank" style="text-decoration: none; color: inherit;">%s</a>',
        urls, x
      )
    )
  }
}

gt_open_bugs_by_year <- function(by_year) {
  year_cols <- setdiff(names(by_year), c("component", "Total"))
  max_n <- max(c(1, unlist(by_year[year_cols])))
  linkable <- by_year$component != "(No component)"

  tbl <- by_year %>%
    gt(rowname_col = "component") %>%
    tab_spanner(label = "Year opened", columns = all_of(year_cols)) %>%
    data_color(
      columns = all_of(year_cols),
      method = "numeric",
      palette = c("#ffffff", "#2a78d6"),
      domain = c(0, max_n)
    ) %>%
    sub_zero(columns = all_of(year_cols), zero_text = "") %>%
    tab_style(
      style = cell_text(weight = "bold"),
      locations = cells_body(columns = Total)
    ) %>%
    tab_options(
      table.width = pct(100),
      container.height = px(600),
      container.overflow.y = TRUE
    )

  for (col in c(year_cols, "Total")) {
    year <- if (col == "Total") NULL else as.integer(col)
    urls <- ifelse(linkable, bug_search_url(by_year$component, year), NA)
    tbl <- tbl %>%
      text_transform(
        locations = cells_body(columns = all_of(col)),
        fn = link_cells(urls)
      )
  }

  tbl
}

# Monthly snapshots of how many bugs opened before `cutoff` were still open on
# each date, reconstructed from created/closed dates. Uses current labels, so a
# bug relabelled recently is shown under its current component for all dates.
old_bug_burndown <- function(bugs, cutoff = old_bug_cutoff,
                             months_back = 18, top_n = 4) {
  old <- bugs %>% filter(created < cutoff)

  snapshot_dates <- unique(c(
    seq(
      lubridate::floor_date(Sys.Date() %m-% months(months_back), "month"),
      lubridate::floor_date(Sys.Date(), "month"),
      by = "month"
    ),
    Sys.Date()
  ))

  counts <- purrr::map_dfr(snapshot_dates, function(d) {
    old %>%
      filter(created <= d, is.na(closed) | closed > d) %>%
      count(component, name = "n") %>%
      mutate(date = d)
  })

  top_components <- counts %>%
    filter(date == max(date)) %>%
    arrange(desc(n)) %>%
    slice_head(n = top_n) %>%
    pull(component)

  # "Component: Other" is a real label, so the collapsed bucket needs its own name
  rest <- "All other components"

  counts %>%
    mutate(
      component = ifelse(component %in% top_components, component, rest),
      component = factor(component, levels = c(top_components, rest))
    ) %>%
    count(date, component, wt = n, name = "n")
}

plot_old_bug_burndown <- function(burndown) {
  # Named components get hues in fixed order; the catch-all band is always grey
  palette <- c("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4")
  components <- levels(burndown$component)
  named <- head(components, -1)
  stopifnot(length(named) <= length(palette))
  component_colours <- c(
    setNames(palette[seq_along(named)], named),
    setNames("#9a9a94", tail(components, 1))
  )

  ggplot2::ggplot(burndown, ggplot2::aes(x = date, y = n, fill = component)) +
    ggplot2::geom_area(colour = "white", linewidth = 0.3) +
    ggplot2::scale_x_date(date_breaks = "3 months", date_labels = "%b %Y") +
    ggplot2::scale_y_continuous(expand = ggplot2::expansion(mult = c(0, 0.05))) +
    ggplot2::scale_fill_manual(values = component_colours, name = NULL) +
    ggplot2::labs(x = NULL, y = "Open bugs") +
    ggplot2::theme_minimal() +
    ggplot2::theme(
      axis.text.x = ggplot2::element_text(angle = 45, hjust = 1),
      legend.position = "top",
      panel.grid.minor = ggplot2::element_blank()
    )
}
