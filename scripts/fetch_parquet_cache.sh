#!/bin/bash
# Download parquet files from arrow-gh-cache release
# Run this before rendering the dashboard locally

CACHE_DIR="data/cache"
BASE_URL="https://github.com/thisisnic/arrow-gh-cache/releases/download/cache-latest"

mkdir -p "$CACHE_DIR"

for file in open_prs.parquet closed_prs.parquet open_issues.parquet closed_issues.parquet; do
  echo "Downloading $file..."
  curl -sL "$BASE_URL/$file" -o "$CACHE_DIR/$file"
done

echo "Done."
