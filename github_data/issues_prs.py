import requests
import datetime
import os

GH_API_TOKEN = os.environ['GH_API_TOKEN']

def parse_gh_date(date):
    return datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")

def get_all_prs():
    """ Get all open PRs from the Apache Arrow repo"""
    prs = []
    page_num=1
    while True:
            open_prs = requests.get("https://api.github.com/repos/apache/arrow/pulls?per_page=100&page=%s" % page_num, 
    headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GH_API_TOKEN}"})
            prs.extend(open_prs.json())

            # the response is paginated, so we need to check for a link to the next page
            if 'rel="next"' in open_prs.headers["Link"]:
                page_num += 1
            else:
                break
    return prs  

def extract_prs(prs, component):
    """ Extract PRs labelled with a particular component from a list of PRs 
    
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
    for pr in prs:
        for label in pr['labels']:
            if component in label['name']:
                pr["created_at"] = parse_gh_date(pr["created_at"])
                relevant_prs.append(pr)
                break
    return relevant_prs

def get_all_issues(component_label):
    """ Get all open issues from the Apache Arrow repo that are labelled with a particular component"""
    issues = []
    page_num=1
    while True:
            open_issues = requests.get("https://api.github.com/repos/apache/arrow/issues?labels=%s&per_page=100&page=%s" % (component_label, page_num), 
    headers={"Accept": "application/vnd.github.v3+json", "Authorization": f"token {GH_API_TOKEN}"})
            issues.extend(open_issues.json())

            # the response is paginated, so we need to check for a link to the next page
            if 'rel="next"' in open_issues.headers["Link"]:
                page_num += 1
            else:
                break
                
    # GitHub consider both issues and PRs as issues, so we should filter out the PRs            
    not_prs = []
    for i in issues:
        if 'pull_request' not in i:
            not_prs.append(i)
    
    return not_prs

def extract_bugs(issues):
    
    """ Extract PRs labelled 'Type: bug' and their triage status from a list of issues 
    
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
        for label in i['labels']:
            if label['name'] == 'Type: bug':
                bugs.append(i)
                break
    
    # get triage status
    triage_status = {"triaged": {"blocker": [], "critical": [], "other": []}, "untriaged": []}
    for bug in bugs:
        assigned = False
        bug["created_at"] = parse_gh_date(bug['created_at'])
        for label in bug['labels']:
            if label['name'].startswith('Priority: Blocker'):
                triage_status["triaged"]["blocker"].append(bug)
                assigned = True
                break
            elif label['name'].startswith('Priority: Critical'):
                triage_status["triaged"]["critical"].append(bug)
                assigned = True
                break
            elif label['name'].startswith('Priority'):
                triage_status["triaged"]["other"].append(bug)
                assigned = True
                break
        if assigned == False:
            triage_status["untriaged"].append(bug)
            
    return triage_status

