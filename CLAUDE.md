
# Arrow Dash 

A Quarto dashboard for simplifying project maintenance and monitoring important metrics for tracking project sustainability.
It is a static dashboard which is deployed via GitHub Actions.
It is written in a mix of Python and R. It is not desirable to go only in one language.

## Key Components

### Per-language summaries (Issues & PRs page)

The dashboard contains per-language tabs for Python, R, and C++.
Each language tab contains:
- Valueboxes showing open issues/PRs count and issues/PRs from new contributors
- Tables of open issues and PRs from last 90 days (new contributors highlighted)

Note: There are hidden "Dummy" tabs to work around a Quarto bug where even-positioned tabs
get inverted layout orientation. See custom.scss for the CSS that hides them.

### Home page

Links to useful Arrow project resources for maintainers across all languages.

### Project Health page

- Various plots and metrics, showing commits, PRs opened/closed and issues opened/closed over the past 18 months
- Also shows changes in open issues/PRs and change since a month ago

### Onboarding page

- Community/new contributor tracking and metrics

## Key files to understand

For future AI assistants working on this project, read these help pages via btw tools:

- 

Web fetch these pages:

- https://quarto.org/docs/dashboards/
- https://quarto.org/docs/dashboards/layout.html
- https://quarto.org/docs/dashboards/data-display.html
- https://quarto.org/docs/dashboards/parameters.html
-

## Important information to keep in mind

GitHub API Limitations:
  1. Search API rate limit: Only 30 requests/minute (vs 5000/hour for regular API)
  2. 1,000 result cap: Can only retrieve first 1,000 results from any search
  3. Inaccurate total_count: Shows theoretical matches, not accessible results

Ways around this:
- for totals, use total_count from search API - this is fine for current open issues/PRs since it's just a
  snapshot
- or use loops and process by-week
- for counting monthly commits you can use the `/repos/:owner/:repo/commits` endpoint with .limit = Inf, which handles pagination
  automatically and doesn't use the search API.

## Re-rendering the dashboard

To re-render the dashboard, we have to activate the virtual environment and then call quarto:

```
source ~/.virtualenvs/r-arrow-dash/bin/activate
quarto render index.qmd
```