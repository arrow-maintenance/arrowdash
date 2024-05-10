# MIT license

# Copyright (c) 2024 ???

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from datetime import (date, datetime, timedelta)
import cmd, os
import requests

GH_API_TOKEN = os.environ['GH_API_TOKEN']
HTTP_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GH_API_TOKEN}",
}


def select_subset_of_issue_items(issue):
    """
    Select main information from the issue query.

    Parameters
    ----------
    issue: dict
        Dictionary of issues information returned from GitHub API call

    Returns
    -------
    dict : main information selected from the input dict (issue url,
           title, state, creator, assignee, milestone, number of comments, date
           it was created)
    """
    new_list = {}
    new_list["creator"] = issue["user"]["login"]
    
    list_of_info = [
        "url",
        "title",
        "state",
        "assignee",
        "milestone",
        "comments",
        "created_at",
    ]
    for info in list_of_info:
        new_list[info] = issue[info]

    new_list["labels"] = issue["labels"][0]["name"]

    return new_list


def issues_from_last_month(status):
    """
    Get issues and PRs created by a new contributor in
    the last month with the GitHub API call.

    New contributor is selected by the author_association from the
    issue descriptions which can be: None, COLLABORATOR, CONTRIBUTOR
    or MEMBER.

    Parameters
    ----------
    status : string
        Is the issue still open or already closed
    
    Returns
    -------
    new_contributors_issues, new_contributors_pr : tuple
        first is a list of issues created by new contributors, second
        is a list of PRs created by new contributors
    """
    new_contributors_issues = []
    new_contributors_pr = []

    last_month = date.today() - timedelta(days=31)
    last_month = last_month.strftime("%Y-%m-%dT%H:%M:%SZ")

    page_number = 1
    while True:
        resp = requests.get(
            "https://api.github.com/repos/apache/arrow/issues",
            params={
                "state": status,
                "labels": "Component: Python",
                "since": last_month,
                "per_page": 100,
                "page": page_number,
            },
            headers=HTTP_HEADERS,
        )

        for item in resp.json():
            if item["author_association"] == "NONE":
                if "pull_request" in item:
                    item["created_at"] = datetime.strptime(
                        item["created_at"], "%Y-%m-%dT%H:%M:%SZ"
                    )
                    new_contributors_pr.append(select_subset_of_issue_items(item))

                else:
                    new_contributors_issues.append(select_subset_of_issue_items(item))

        # search through all pages from the REST API
        if "Link" in resp.headers and 'rel="next"' in resp.headers["Link"]:
                page_number += 1
        else:
            break

    return new_contributors_issues, new_contributors_pr


def group_issues_by_labels(status):
    """
    Group list of open issues created by a new contributor in
    the last month by labels.

    New contributor is selected by the author_association from the
    issue descriptions which can be: None, COLLABORATOR, CONTRIBUTOR
    or MEMBER.

    Issues contain main information (issue url, title, state, creator,
    assignee, milestone, number of comments, date it was created) as a
    dictionary.

    Parameters
    ------------
    status : string
        Is the issue still open or already closed

    Return
    -----------
    grouped_issues : dictionary
        Dictionary containing items grouped by label such as bug,
        enhancement, task, test or usage.
    """
    issues, _ = issues_from_last_month(status)

    grouped_issues = {
        "Bug": [], "Enhancement": [], "Task": [], "Test": [], "Usage": []
    }

    for issue in issues:
        # issue["created_at"] = datetime.strptime(issue['created_at']["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        label = issue["labels"]
        if label == "Type: bug":
            grouped_issues["Bug"].append(issue)
        elif label == "Type: enhancement":
            grouped_issues["Enhancement"].append(issue)
        elif label == "Type: task":
            grouped_issues["Task"].append(issue)
        elif label == "Type: test":
            grouped_issues["Test"].append(issue)
        elif label == "Type: usage":
            grouped_issues["Usage"].append(issue)

    return grouped_issues
