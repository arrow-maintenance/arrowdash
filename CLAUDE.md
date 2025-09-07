
# Arrow Dash 

A Quarto dashboard for simplifying project maintenance and monitoring important metrics for tracking project sustainability.
It is a static dashboard which is deployed via GitHub Actions.
It is written in a mix of Python and R. It is not desirable to go only in one language.

## Key Components

### Per-language summaries

The dashboard contains per-language pages for Python and R, though this could be extended.
Each language-based page contains the following tabs:
- Summary
    - showing how many open issues, PRs, stack overflow questions, and mailing list messages there are for the past few months
    - Bar plots of issues opebned by new and existing contributors over the past 3 months
- Issues
    - boxes showing numbers of open issues, issues from new contributors and issues with no replies
    - a table of issues with ones from new contributors highlights
- PRs
    - (as for issues but for pull requests)
- Stack Overflow
    - summarising questions from SO
- Mailing List
    - ANy maililng list conversations which are relevant

### Overall Summary

A page which takes the month's activity on the mailing list and provides a high-level summary of it

### Maintenance stats

- Various plots and matetrics, showing commits, PRs opened/closed and issues opened/closed over the past 18 months.
- Also shows changes in open issues/PRs and change since a month ago

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