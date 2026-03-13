# GitHub Data Cache

Parquet files caching Apache Arrow GitHub data to avoid API rate limits.

## Files

### issue_details.parquet
Open issues only. Columns: `number`, `title`, `state`, `created_at`, `updated_at`, `user_login`, `body`, `labels`, `assignees`, `html_url`

### pr_details.parquet
All PRs (open and closed). Columns: `number`, `title`, `state`, `draft`, `created_at`, `updated_at`, `closed_at`, `merged_at`, `user_login`, `author_association`, `body`, `labels`, `assignees`, `html_url`, `head_ref`, `base_ref`

### contributors.parquet
All repo contributors. Columns: `login`, `id`, `type`, `contributions`, `html_url`, `avatar_url`, `site_admin`, `first_pr` (PR number of first PR, NA for commit-only contributors)

## Updating

- Initial population: run scripts in `scripts/gh_cache/initialisation/`
- Incremental updates: run `scripts/gh_cache/fetch_yesterday_activity.R`
