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

import datetime


def parse_gh_date(date):
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")


def extract_prs(data, component):
    """Extract PRs labelled with a particular component from a list of PRs

    Parameters
    ------------
        prs: list
            JSON list of PRs returned from GitHub API call

    Return
    -----------
        r_prs : list
            JSON list of PRs returned from GitHub API call that have the specified `component` label


    """
    relevant_prs = []
    for item in data:
        for label in item["labels"]:
            if label["name"] == "Component: " + component:
                if "pull_request" in item:
                    item["created_at"] = parse_gh_date(item["created_at"])
                relevant_prs.append(item)
                break
    return relevant_prs


def get_all_issues(data, component):
    """Get all open issues from the Apache Arrow repo that are labelled with a particular component"""
    not_prs = []
    for item in data:
        for label in item["labels"]:
            if label["name"] == "Component: " + component:
                if "pull_request" not in item:
                    item["created_at"] = parse_gh_date(item["created_at"])
                not_prs.append(item)
                break
    return not_prs


def extract_bugs(issues):
    """Extract PRs labelled 'Type: bug' and their triage status from a list of issues

    Parameters
    ------------
        r_issues: list
            JSON list of issues returned from GitHub API call

    Return
    -----------
        triage_status : dictionary
            Dictionary containing items "triaged" and "untriaged" based
             on whether bugs have a "Priority" label assigned or not


    """

    # get all bugs
    bugs = []
    for i in issues:
        for label in i["labels"]:
            if label["name"] == "Type: bug":
                bugs.append(i)
                break

    # get triage status
    triage_status = {
        "triaged": {"blocker": [], "critical": [], "other": []},
        "untriaged": [],
    }
    for bug in bugs:
        assigned = False
        bug["created_at"] = parse_gh_date(bug["created_at"])
        for label in bug["labels"]:
            if label["name"].startswith("Priority: Blocker"):
                triage_status["triaged"]["blocker"].append(bug)
                assigned = True
                break
            elif label["name"].startswith("Priority: Critical"):
                triage_status["triaged"]["critical"].append(bug)
                assigned = True
                break
            elif label["name"].startswith("Priority"):
                triage_status["triaged"]["other"].append(bug)
                assigned = True
                break
        if assigned == False:
            triage_status["untriaged"].append(bug)

    return triage_status
