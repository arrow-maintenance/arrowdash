"""
Update daily open issue/PR counts snapshot.

Output file:
  - data/open_counts.csv
"""

import logging
import os
import sys
from datetime import date

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_helpers import gh_search_count, OWNER, REPO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    logging.info("=== Updating open counts ===")
    os.makedirs("data", exist_ok=True)

    today = date.today()
    csv_path = "data/open_counts.csv"

    open_issues = gh_search_count(f"repo:{OWNER}/{REPO} is:issue state:open")
    open_prs = gh_search_count(f"repo:{OWNER}/{REPO} is:pr state:open")

    new_row = pd.DataFrame([{"date": today, "open_issues": open_issues, "open_prs": open_prs}])

    if os.path.exists(csv_path):
        existing = pd.read_csv(csv_path, parse_dates=["date"])
        existing["date"] = existing["date"].dt.date
        if today in existing["date"].values:
            logging.info("Open counts already recorded for today")
            return
        df = pd.concat([existing, new_row], ignore_index=True)
    else:
        df = new_row

    df.to_csv(csv_path, index=False)
    logging.info(f"Recorded: {open_issues} issues, {open_prs} PRs")


if __name__ == "__main__":
    main()
