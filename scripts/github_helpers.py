"""Shared GitHub API helpers for data update scripts."""

import logging
import os
from datetime import date, timedelta

import requests

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

OWNER = "apache"
REPO = "arrow"


def fetch_gh_issue_pr_data(months=3):
    """Fetch issues and PRs updated in last N months."""
    logging.info("Fetching GitHub issue/PR data")
    data = []
    cutoff = date.today() - timedelta(days=months * 30)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    page = 1
    while True:
        logging.info(f"  Fetching page {page}")
        resp = requests.get(
            f"https://api.github.com/repos/{OWNER}/{REPO}/issues",
            params={"state": "all", "since": cutoff_str, "per_page": 100, "page": page},
            headers=HTTP_HEADERS,
        )
        resp.raise_for_status()
        items = resp.json()
        data.extend(items)

        if "Link" in resp.headers and 'rel="next"' in resp.headers["Link"]:
            page += 1
        else:
            break

    logging.info(f"  Fetched {len(data)} items total")
    return data


def gh_search_count(query):
    """Get total_count from GitHub search API."""
    resp = requests.get(
        "https://api.github.com/search/issues",
        params={"q": query},
        headers=HTTP_HEADERS,
    )
    resp.raise_for_status()
    return resp.json()["total_count"]


def fetch_commits(since, until):
    """Fetch commits between two dates."""
    commits = []
    page = 1
    while True:
        resp = requests.get(
            f"https://api.github.com/repos/{OWNER}/{REPO}/commits",
            params={
                "since": f"{since}T00:00:00Z",
                "until": f"{until}T00:00:00Z",
                "per_page": 100,
                "page": page,
            },
            headers=HTTP_HEADERS,
        )
        resp.raise_for_status()
        items = resp.json()
        if not items:
            break
        commits.extend(items)
        page += 1
    return commits
