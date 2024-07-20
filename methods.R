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
library(plotly)

create_fig <- function(x, y, y_new){

  fig <-  plot_ly(x = x, y = y, type = 'bar',
          name = 'Other contributors', marker = list(color = 'FBCD99'))
  if (nrow(y_new)) {
    fig <- fig %>% add_trace(y = ~y_new, name = 'New contributors', marker = list(color = '#DCAAA6'))
  }
  fig <- fig %>% layout(plot_bgcolor='#E9EEEF',
          xaxis = list(
            title = "",
            zerolinecolor = '#ffff',
            zerolinewidth = 2,
            gridcolor = 'ffff'),
          yaxis = list(
            title = "",
            zerolinecolor = '#ffff',
            zerolinewidth = 2,
            gridcolor = 'ffff'))

  fig
}

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

dt_show_emails <- function(x){

  DT::datatable(
    escape = FALSE,
    x
  )
}
