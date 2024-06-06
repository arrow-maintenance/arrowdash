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

    new_list["labels"] = [i["name"] for i in issue["labels"]]

    return new_list


def issues(data, status, component):
    """
    Get issues and PRs created by a new contributor in
    the last 3 months.

    New contributor is selected by the author_association from the
    issue descriptions which can be: None, COLLABORATOR, CONTRIBUTOR
    or MEMBER.

    Parameters
    ----------
    data : list
        List of issues
    status : string
        Is the issue still open or already closed
    component : string
        Python or R.

    Returns
    -------
    new_contributors_issues, new_contributors_pr : tuple
        first is a list of issues created by new contributors, second
        is a list of PRs created by new contributors
    """
    issues = []
    prs = []

    if status not in ["open", "closed"]:
        raise ValueError("State can be 'open' or 'closed'.")
    if component not in ["Python", "R"]:
        raise ValueError("Component can be 'Python' or 'R'.")

    for item in data:
        if item["author_association"] == "NONE" and item["state"] == status:
            for label in item["labels"]:
                if label["name"] == "Component: " + component:
                    if "pull_request" in item:
                        prs.append(select_subset_of_issue_items(item))
                    else:
                        issues.append(select_subset_of_issue_items(item))

    return issues, prs


def issues_by_labels(data, status, component):
    """
    Group list of open issues (created by a new contributor in
    the last month) by labels.

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
    issues_list, _ = issues(data, status, component)

    grouped_issues = {"Bug": [], "Enhancement": [], "Task": [], "Test": [], "Usage": []}

    for issue in issues_list:
        # issue["created_at"] = datetime.strptime(issue['created_at']["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        label = issue["labels"]
        if "Type: bug" in label:
            grouped_issues["Bug"].append(issue)
        elif "Type: enhancement" in label:
            grouped_issues["Enhancement"].append(issue)
        elif "Type: task" in label:
            grouped_issues["Task"].append(issue)
        elif "Type: test" in label:
            grouped_issues["Test"].append(issue)
        elif "Type: usage" in label:
            grouped_issues["Usage"].append(issue)

    return grouped_issues


def extract_bugs(data):
    # get all bugs
    bugs = []
    for i in data:
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
        # bug["created_at"] = parse_gh_date(bug["created_at"])
        bug["created_at"] = bug["created_at"]
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
