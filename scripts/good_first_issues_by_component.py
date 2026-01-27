"""
Fetch and summarize open good-first-issue issues by component.

This is a utility script for quick analysis, not part of the daily update.
"""

import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_helpers import gh_search_count, HTTP_HEADERS, OWNER, REPO
import requests


def main():
    print("Fetching open good-first-issue issues...")

    # Fetch all matching issues (paginated)
    issues = []
    page = 1
    while True:
        resp = requests.get(
            "https://api.github.com/search/issues",
            params={
                "q": f"repo:{OWNER}/{REPO} is:issue state:open label:good-first-issue",
                "per_page": 100,
                "page": page,
            },
            headers=HTTP_HEADERS,
        )
        resp.raise_for_status()
        data = resp.json()
        issues.extend(data["items"])

        if len(data["items"]) < 100:
            break
        page += 1

    print(f"Found {len(issues)} issues")

    # Extract component labels
    components = Counter()
    for issue in issues:
        issue_components = [
            label["name"].replace("Component: ", "")
            for label in issue["labels"]
            if label["name"].startswith("Component: ")
        ]
        if not issue_components:
            components["(No component)"] += 1
        else:
            for comp in issue_components:
                components[comp] += 1

    # Print summary
    print("\nComponent                    Count")
    print("-" * 40)
    for comp, count in components.most_common():
        print(f"{comp:<30} {count:>5}")

    print(f"\nTotal: {len(issues)} issues across {len(components)} components")


if __name__ == "__main__":
    main()
