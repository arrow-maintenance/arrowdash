# MIT license

# Copyright (c) 2024 ???

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from datetime import date, timedelta, datetime
import os
import requests
import csv
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

GH_API_TOKEN = os.environ.get("GH_API_TOKEN")
if not GH_API_TOKEN:
    logging.error("GitHub API token not found in environment variables.")
    raise EnvironmentError("GH_API_TOKEN environment variable is not set.")

HTTP_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GH_API_TOKEN}",
}

def fetch_gh_issue_pr_data(months = 3):
    """
    Get issues and PRs updated in last three months with the GitHub API call.

    Returns
    -------
    data : list
        list of issues and PRs updated in the last 3 months
    """
    logging.info("Starting to fetch data from GitHub API.")

    data = []

    last_3_months = date.today() - timedelta(days=months*30)
    last_3_months = last_3_months.strftime("%Y-%m-%dT%H:%M:%SZ")

    page_number = 1
    while True:
        logging.info(f"Fetching page {page_number} of issues/PRs updated since {last_3_months}.")

        resp = requests.get(
            "https://api.github.com/repos/apache/arrow/issues",
            params={
                "state": "all",
                "since": last_3_months,
                "per_page": 100,
                "page": page_number,
            },
            headers=HTTP_HEADERS,
        )

        if resp.status_code != 200:
            logging.error(f"Failed to fetch data: {resp.status_code} - {resp.reason}")
            resp.raise_for_status()

        items = resp.json()
        logging.info(f"Fetched {len(items)} items from page {page_number}.")

        data.extend(items)

        # search through all pages from the REST API
        if "Link" in resp.headers and 'rel="next"' in resp.headers["Link"]:
            page_number += 1
        else:
            logging.info("No more pages to fetch.")
            break

    logging.info(f"Finished fetching data. Total items retrieved: {len(data)}.")
    return data

def weekly_items_opened(type="issue", start_date=None, end_date=None):
    """Fetch weekly counts of issues or PRs from start_date to end_date (exclusive), aligned to Sundays."""
    if type not in ("issue", "pr"):
        raise ValueError("type must be 'issue' or 'pr'")

    if start_date is None:
        start_date = datetime.utcnow().date() - timedelta(days=7)
    if end_date is None:
        end_date = datetime.utcnow().date()

    current = start_date
    results = []

    while current < end_date:
        next_week = current + timedelta(days=7)
        date_range = f"{current.isoformat()}..{next_week.isoformat()}"
        query = f"repo:apache/arrow is:{type} created:{date_range}"

        resp = requests.get(
            "https://api.github.com/search/issues",
            params={"q": query},
            headers=HTTP_HEADERS
        )

        if resp.status_code != 200:
            logging.error(f"Error fetching data for {date_range}: {resp.status_code}")
            raise requests.HTTPError(resp.text)

        count = resp.json().get("total_count", 0)
        results.append({
            "week_start": current.isoformat(),
            "n": count
        })

        current = next_week
        time.sleep(2.1)

    return results


def get_last_sunday(today=None):
    if today is None:
        today = datetime.utcnow().date()
    return today - timedelta(days=today.weekday() + 1 if today.weekday() != 6 else 0)


def update_items_csv(type="issue", csv_path="./data/issues_opened.csv"):

    if not os.path.exists(csv_path):
        logging.info(f"{csv_path} not found. Creating new file.")
        existing_data = []
    else:
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)

    # Determine last recorded week
    if existing_data:
        last_week = max(datetime.strptime(row["week_start"], "%Y-%m-%d").date() for row in existing_data)
    else:
        last_week = get_last_sunday() - timedelta(weeks=208)

    next_week = last_week + timedelta(days=7)
    this_sunday = get_last_sunday()

    if next_week >= this_sunday:
        logging.info("Data is already up to date.")
        return

    logging.info(f"Fetching new {type} data from {next_week} to {this_sunday}.")
    new_data = weekly_items_opened(type=type, start_date=next_week, end_date=this_sunday)

    # Append and write out
    all_data = existing_data + new_data
    all_data.sort(key=lambda row: row["week_start"])

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["week_start", "n"])
        writer.writeheader()
        writer.writerows(all_data)

    logging.info(f"Updated {csv_path} with {len(new_data)} new rows.")


def weekly_items_closed(type="issue", start_date=None, end_date=None):
    """Fetch weekly counts of issues or PRs closed from start_date to end_date (exclusive), aligned to Sundays."""
    if type not in ("issue", "pr"):
        raise ValueError("type must be 'issue' or 'pr'")

    if start_date is None:
        start_date = datetime.utcnow().date() - timedelta(days=7)
    if end_date is None:
        end_date = datetime.utcnow().date()

    current = start_date
    results = []

    while current < end_date:
        next_week = current + timedelta(days=7)
        date_range = f"{current.isoformat()}..{next_week.isoformat()}"
        query = f"repo:apache/arrow is:{type} closed:{date_range}"

        resp = requests.get(
            "https://api.github.com/search/issues",
            params={"q": query},
            headers=HTTP_HEADERS
        )

        if resp.status_code != 200:
            logging.error(f"Error fetching data for {date_range}: {resp.status_code}")
            raise requests.HTTPError(resp.text)

        count = resp.json().get("total_count", 0)
        results.append({
            "week_start": current.isoformat(),
            "n": count
        })

        current = next_week
        time.sleep(2.1)

    return results


def update_closed_items_csv(type="issue", csv_path="./data/issues_closed.csv"):

    if not os.path.exists(csv_path):
        logging.info(f"{csv_path} not found. Creating new file.")
        existing_data = []
    else:
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)

    if existing_data:
        last_week = max(datetime.strptime(row["week_start"], "%Y-%m-%d").date() for row in existing_data)
    else:
        last_week = get_last_sunday() - timedelta(weeks=208)

    next_week = last_week + timedelta(days=7)
    this_sunday = get_last_sunday()

    if next_week >= this_sunday:
        logging.info("Closed data is already up to date.")
        return

    logging.info(f"Fetching closed {type} data from {next_week} to {this_sunday}.")
    new_data = weekly_items_closed(type=type, start_date=next_week, end_date=this_sunday)

    all_data = existing_data + new_data
    all_data.sort(key=lambda row: row["week_start"])

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["week_start", "n"])
        writer.writeheader()
        writer.writerows(all_data)

    logging.info(f"Updated {csv_path} with {len(new_data)} new rows.")
