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

from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px


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
        "created_at",
        "author_association",
    ]
    for info in list_of_info:
        new_list[info] = issue[info]

    new_list["labels"] = [i["name"] for i in issue["labels"]]

    return new_list


def get_all(data, component):
    """
    Get issues and PRs from the Apache Arrow repo that were updated in
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
    issues = []
    prs = []
    for item in data:
        for label in item["labels"]:
            if label["name"] == "Component: " + component:
                if "pull_request" in item:
                    prs.append(select_subset_of_issue_items(item))
                else:
                    issues.append(select_subset_of_issue_items(item))
                break

    return pd.DataFrame(issues), pd.DataFrame(prs)


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
    issues : pd.DataFrame
        Pandas data frame with only issues or prs still opened.
    """
    df["url_title"] = (
        '<a target="_blank" href="' + df["html_url"] + '">' +
        df["title"] + "</a>"
    )
    return df[df.state == "open"][
        ["created_at", "url_title", "html_url", "author_association"]
    ]


def get_summary(df):
    """
    Count the number of issues or pull requests by creation date selected from
    the data frame with issues or pull requests. Count only issues or pull requests
    created in last 3 months.

    Parameters
    ----------
    df : pa.DataFrame
        Pandas data frame with all issues or pull requests.

    Returns
    -------
    fig : px.histogram
        Plotly histogram with number of issues or prs created in last 3 months
    """
    last_3_months = datetime.today() - timedelta(days=90)
    df["created_at"] = df["created_at"].apply(lambda x: parse_gh_date(x))
    fig = px.histogram(df[df.created_at > last_3_months],
                       x = "created_at",
                       color = "author_association")

    return fig
