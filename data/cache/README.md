# GitHub Data Cache

Parquet files caching Apache Arrow GitHub data. These files are fetched from the
[arrow-gh-cache](https://github.com/thisisnic/arrow-gh-cache) repo releases and
are not stored in this repository.

## Files

- `open_issues.parquet` / `closed_issues.parquet` — all Apache Arrow issues
- `open_prs.parquet` / `closed_prs.parquet` — all Apache Arrow PRs

## Updating

Run `scripts/fetch_parquet_cache.sh` to download the latest files locally.
In CI, files are downloaded automatically during the workflow.
