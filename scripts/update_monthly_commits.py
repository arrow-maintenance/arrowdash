"""
Update monthly commit counts.

Output file:
  - data/monthly_commit_counts.csv
"""

import logging
import os
import sys
from datetime import date, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_helpers import fetch_commits

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    logging.info("=== Updating monthly commit counts ===")
    os.makedirs("data", exist_ok=True)

    csv_path = "data/monthly_commit_counts.csv"
    current_month = date.today().strftime("%Y-%m")
    month_start = date.today().replace(day=1)

    if os.path.exists(csv_path):
        existing = pd.read_csv(csv_path)
    else:
        existing = pd.DataFrame(columns=["month", "commit_count"])

    # Current month (running total)
    commits = fetch_commits(month_start, date.today() + timedelta(days=1))
    current_count = len(commits)

    if current_month in existing["month"].values:
        existing.loc[existing["month"] == current_month, "commit_count"] = current_count
        logging.info(f"Updated {current_month}: {current_count} commits")
    else:
        existing = pd.concat([existing, pd.DataFrame([{"month": current_month, "commit_count": current_count}])],
                            ignore_index=True)
        logging.info(f"Added {current_month}: {current_count} commits")

    existing.to_csv(csv_path, index=False)


if __name__ == "__main__":
    main()
