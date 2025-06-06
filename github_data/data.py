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

