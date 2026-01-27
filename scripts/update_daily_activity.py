"""
Update daily issue/PR opened/closed counts.

Output files:
  - data/issues_opened_daily.csv
  - data/issues_closed_daily.csv
  - data/prs_opened_daily.csv
  - data/prs_closed_daily.csv
"""

import logging
import os
import sys
import time
from datetime import date, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_helpers import gh_search_count, OWNER, REPO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    logging.info("=== Updating daily activity counts ===")
    os.makedirs("data", exist_ok=True)

    configs = [
        ("issue", "created", "data/issues_opened_daily.csv"),
        ("issue", "closed", "data/issues_closed_daily.csv"),
        ("pr", "created", "data/prs_opened_daily.csv"),
        ("pr", "closed", "data/prs_closed_daily.csv"),
    ]

    today = date.today()
    yesterday = today - timedelta(days=1)

    for item_type, state, csv_path in configs:
        if os.path.exists(csv_path):
            existing = pd.read_csv(csv_path, parse_dates=["date"])
            existing["date"] = existing["date"].dt.date
            last_date = existing["date"].max()
        else:
            existing = pd.DataFrame(columns=["date", "n"])
            last_date = today - timedelta(days=30)

        start_date = last_date + timedelta(days=1)
        if start_date > yesterday:
            logging.info(f"{state} {item_type}s: up to date")
            continue

        logging.info(f"Updating {state} {item_type}s from {start_date} to {yesterday}")
        new_rows = []
        current = start_date
        while current <= yesterday:
            query = f"repo:{OWNER}/{REPO} is:{item_type} {state}:{current.strftime('%Y-%m-%d')}"
            count = gh_search_count(query)
            new_rows.append({"date": current, "n": count})
            logging.info(f"  {current}: {count}")
            current += timedelta(days=1)
            time.sleep(2.1)  # Rate limit: 30 requests/minute

        if new_rows:
            new_df = pd.DataFrame(new_rows)
            df = pd.concat([existing, new_df], ignore_index=True)
            df.to_csv(csv_path, index=False)


if __name__ == "__main__":
    main()
