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
from datetime import date, datetime, timedelta
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def parse_gh_date(date):
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")

def select_subset_of_issue_items(issue):
    """
    Select main information from the issue query.

    Parameters
    ----------
    issue: dict
        Dictionary of issues information returned from GitHub API call

    Returns
    -------
    dict : main information selected from the input dict (url,
           title, state, milestone, date it was created)
    """
    new_list = {}

    list_of_info = [
        "html_url",
        "title",
        "state",
        "milestone",
        "comments",
        "created_at",
        "author_association",
    ]
    for info in list_of_info:
        new_list[info] = issue[info]

    new_list["labels"] = [i["name"] for i in issue["labels"]]

    return new_list

def get_all(data, component):
    """
    Get issues and PRs from the Apache Arrow repo that were created in
    the last 3 months and are labelled with a particular component.

    Parameters
    ----------
    component : string
        Python or R.

    Returns
    -------
    issues : pd.DataFrame
        Pandas data frame with issue information in row.
    """
    logging.info(f"Starting data filtering for component: {component}")

    issues = []
    prs = []

    last_3_months = date.today() - timedelta(days=90)
    last_3_months = last_3_months.strftime("%Y-%m-%dT%H:%M:%SZ")

    for item in data:
        if item["created_at"] > last_3_months:
            for label in item["labels"]:
                if label["name"] == "Component: " + component:
                    if "pull_request" in item:
                        prs.append(select_subset_of_issue_items(item))
                    else:
                        issues.append(select_subset_of_issue_items(item))
                    break

    issues_df = pd.DataFrame(issues)
    prs_df = pd.DataFrame(prs)

    logging.info(f"Filtered {len(issues)} issues and {len(prs)} pull requests.")

    return issues_df, prs_df

def get_open(df):
    """
    Select issues or pull requests that are still opened from
    the data frame of all issues or pull requests. Only
    relevant information for creating a list of open issues and
    prs is kept (date, title with url, html url and author_association)

    Parameters
    ----------
    df : pa.DataFrame
        Pandas data frame with all issues or pull requests.

    Returns
    -------
    df : pd.DataFrame
        Pandas data frame with only issues or prs still opened.
    """
    logging.info("Filtering open issues/pull requests.")

    df["url_title"] = (
        '<a target="_blank" href="' + df["html_url"] + '">' + df["title"] + "</a>"
    )
    open_df = df[df.state == "open"][
        ["created_at", "url_title", "html_url", "author_association", "comments"]
    ]

    logging.info(f"Found {len(open_df)} open issues/pull requests.")

    return open_df

def get_summary(df):
    """
    Count the number of issues or pull requests by week selected from the data
    frame with issues or pull requests. Count only issues or pull requests
    created in last 3 months.

    Parameters
    ----------
    df : pa.DataFrame
        Pandas data frame with all issues or pull requests.
    Returns
    -------
    df_new_contrib, df_others : pd.DataFrame, pd.DataFrame
        Two pandas data frames with number of issues or prs created in last
        3 months grouped by week first by new contributors, second by all
        others.
    """
    logging.info("Creating summary of issues/pull requests.")

    last_3_months = datetime.today() - timedelta(days=90)
    df["created_at"] = df["created_at"].apply(lambda x: parse_gh_date(x))

    df_new_contrib = df[["created_at", "labels"]][
        (df.created_at > last_3_months)
        & (df.author_association.isin(["NONE", "FIRST_TIME_CONTRIBUTOR"]))
    ]
    df_new_contrib = (
        df_new_contrib.groupby([pd.Grouper(key="created_at", freq="1W")])
        .count()
        .reset_index()
    )
    df_new_contrib = df_new_contrib.rename(columns={"labels": "sum"})

    df_others = df[["created_at", "labels"]][
        (df.created_at > last_3_months)
        & (~df.author_association.isin(["NONE", "FIRST_TIME_CONTRIBUTOR"]))
    ]
    df_others = (
        df_others.groupby([pd.Grouper(key="created_at", freq="1W")])
        .count()
        .reset_index()
    )
    df_others = df_others.rename(columns={"labels": "sum"})

    logging.info("Summary created successfully.")

    return df_new_contrib, df_others
