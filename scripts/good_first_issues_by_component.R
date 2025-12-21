library(gh)
library(dplyr)
library(purrr)
library(stringr)
library(tibble)

# Fetch all open "good-first-issue" issues in a single paginated call
message("Fetching open good-first-issue issues...")

issues <- gh(
  "/search/issues",
  q = "repo:apache/arrow is:issue state:open label:good-first-issue",
  .limit = Inf
)

message(sprintf("Found %d issues", length(issues$items)))

# Extract component labels from each issue
extract_components <- function(issue) {
  labels <- map_chr(issue$labels, "name")
  components <- labels[str_starts(labels, "Component: ")]
  if (length(components) == 0) {
    return(tibble(component = "(No component)"))
  }
  tibble(component = str_remove(components, "^Component: "))
}

# Build a table of all component assignments
component_data <- map_dfr(issues$items, extract_components)

# Count by component
summary <- component_data |>
  count(component, name = "open_good_first_issues") |>
  arrange(desc(open_good_first_issues))

print(summary, n = Inf)

message(sprintf("\nTotal: %d issues across %d components",
                sum(summary$open_good_first_issues),
                nrow(summary)))
