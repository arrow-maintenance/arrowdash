"""
Update language-specific data (Python and R issues, PRs, mailing list).

Output files:
  - data/{lang}_issues_open.csv
  - data/{lang}_prs_open.csv
  - data/{lang}_issues_summary.csv
  - data/{lang}_prs_summary.csv
  - data/{lang}_mailing_list.csv
"""

import logging
import os
import sys
from datetime import date, datetime, timedelta

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.github_helpers import fetch_gh_issue_pr_data
import ml_data.data_methods as ml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_gh_date(date_str):
    """Parse GitHub date string."""
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def filter_by_component(data, component):
    """Filter issues/PRs by component label."""
    issues = []
    prs = []
    cutoff = date.today() - timedelta(days=90)
    cutoff_str = cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")

    for item in data:
        if item["created_at"] > cutoff_str:
            for label in item.get("labels", []):
                if label["name"] == f"Component: {component}":
                    record = {
                        "html_url": item["html_url"],
                        "title": item["title"],
                        "state": item["state"],
                        "comments": item["comments"],
                        "created_at": item["created_at"],
                        "author_association": item["author_association"],
                    }
                    if "pull_request" in item:
                        prs.append(record)
                    else:
                        issues.append(record)
                    break

    return pd.DataFrame(issues), pd.DataFrame(prs)


def get_open_items(df):
    """Filter to open items and format for display."""
    if df.empty:
        return pd.DataFrame(columns=["created_at", "url_title", "html_url", "author_association", "comments"])

    df = df.copy()
    df["url_title"] = '<a target="_blank" href="' + df["html_url"] + '">' + df["title"] + "</a>"
    open_df = df[df["state"] == "open"][["created_at", "url_title", "html_url", "author_association", "comments"]]
    return open_df


def get_summary(df):
    """Get weekly summary counts for charts."""
    if df.empty:
        return pd.DataFrame(columns=["date", "others", "new"])

    df = df.copy()
    cutoff = datetime.today() - timedelta(days=90)
    df["created_at"] = df["created_at"].apply(parse_gh_date)

    # New contributors
    new_mask = (df["created_at"] > cutoff) & df["author_association"].isin(["NONE", "FIRST_TIME_CONTRIBUTOR"])
    df_new = df[new_mask].groupby(pd.Grouper(key="created_at", freq="1W")).size().reset_index(name="new")

    # Other contributors
    other_mask = (df["created_at"] > cutoff) & ~df["author_association"].isin(["NONE", "FIRST_TIME_CONTRIBUTOR"])
    df_others = df[other_mask].groupby(pd.Grouper(key="created_at", freq="1W")).size().reset_index(name="others")

    # Merge on date
    df_others["date"] = df_others["created_at"].dt.strftime("%Y-%m-%d")
    df_new["date"] = df_new["created_at"].dt.strftime("%Y-%m-%d")

    summary = df_others[["date", "others"]].merge(df_new[["date", "new"]], on="date", how="outer").fillna(0)
    summary["others"] = summary["others"].astype(int)
    summary["new"] = summary["new"].astype(int)
    summary = summary.sort_values("date")

    return summary


def process_language_data(gh_data, lang):
    """Process all data for a language and save CSVs."""
    logging.info(f"Processing {lang} data")
    lang_lower = lang.lower()

    issues_df, prs_df = filter_by_component(gh_data, lang)

    # Open issues/PRs
    issues_open = get_open_items(issues_df)
    prs_open = get_open_items(prs_df)

    issues_open.to_csv(f"data/{lang_lower}_issues_open.csv", index=False)
    prs_open.to_csv(f"data/{lang_lower}_prs_open.csv", index=False)
    logging.info(f"  Wrote {lang_lower}_issues_open.csv ({len(issues_open)} rows)")
    logging.info(f"  Wrote {lang_lower}_prs_open.csv ({len(prs_open)} rows)")

    # Summaries for charts
    issues_summary = get_summary(issues_df)
    prs_summary = get_summary(prs_df)

    issues_summary.to_csv(f"data/{lang_lower}_issues_summary.csv", index=False)
    prs_summary.to_csv(f"data/{lang_lower}_prs_summary.csv", index=False)
    logging.info(f"  Wrote {lang_lower}_issues_summary.csv")
    logging.info(f"  Wrote {lang_lower}_prs_summary.csv")

    # Mailing list
    try:
        ml_df = ml.get_all(lang)
        ml_df.to_csv(f"data/{lang_lower}_mailing_list.csv", index=False)
        logging.info(f"  Wrote {lang_lower}_mailing_list.csv ({len(ml_df)} rows)")
    except Exception as e:
        logging.warning(f"  Failed to get mailing list for {lang}: {e}")
        pd.DataFrame(columns=["date", "url_title"]).to_csv(f"data/{lang_lower}_mailing_list.csv", index=False)


def main():
    logging.info("=== Updating language-specific data ===")
    os.makedirs("data", exist_ok=True)

    # Fetch GitHub data
    gh_data = fetch_gh_issue_pr_data()

    # Download user mailing list
    logging.info("Downloading user mailing list")
    ml.get_messages("user")

    # Process each language
    for lang in ["Python", "R"]:
        process_language_data(gh_data, lang)

    logging.info("=== Language data update complete ===")


if __name__ == "__main__":
    main()
