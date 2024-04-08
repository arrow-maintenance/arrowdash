import requests
import datetime
import os

GH_API_TOKEN = os.environ['GH_API_TOKEN']
ZULIP_WEBHOOK = os.environ['ZULIP_WEBHOOK']

DEBUG = False

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

def summarise_issue(issue):
    msg = "• <%s|GH-%s: %s>" %  (issue["html_url"], issue["number"], issue["title"]) + "\n"
    return msg

def generate_message(bugs, prs):
    
    one_month = (datetime.datetime.now() - datetime.timedelta(days = 31))
    two_months = (datetime.datetime.now() - datetime.timedelta(days = 62))
    past_month = [bug for bug in bugs["untriaged"] if bug['created_at'] > one_month]
    older_untriaged_bugs = [bug for bug in bugs["untriaged"] if bug['created_at'] <= one_month]

    past_month_message = "\n"
    if(len(past_month) > 0):
        for bug in past_month:
            # need backticks around the title for lazy escaping of special characters
            past_month_message += summarise_issue(bug)
    else:
        past_month_message += "\n* _No bugs to triage!_"

    blockers_message = ""
    blockers = [bug for bug in bugs["triaged"]["blocker"] if bug['created_at'] > two_months]
    for bug in blockers:
        blockers_message += summarise_issue(bug)

    critical_message = ""
    critical = [bug for bug in bugs["triaged"]["critical"] if bug['created_at'] > two_months]

    for bug in critical:
        critical_message += summarise_issue(bug)

    others_message = ""
    others = [bug for bug in bugs["triaged"]["other"] if bug['created_at'] > two_months]
    for bug in others:
        others_message += summarise_issue(bug)

    older = []
    older.extend([bug for bug in bugs["triaged"]["blocker"] if bug['created_at'] < two_months])
    older.extend([bug for bug in bugs["triaged"]["critical"] if bug['created_at'] < two_months])
    older.extend([bug for bug in bugs["triaged"]["other"] if bug['created_at'] < two_months])
    
    prs_message = ""
    for pr in prs:
        prs_message += summarise_issue(pr)
    
    message = {"to_triage": "", "to_fix": "", "prs": ""}
    message["to_triage"] += ":beetle: *Need triage (%s)* :beetle:" % len(past_month) + "\n"
    message["to_triage"] += past_month_message + "\n"
    message["to_triage"] += ("*Untriaged bugs older than 1 month: <https://github.com/apache/arrow/issues?q=is%3Aissue+is%3Aopen+label%3A%22Component%3A+R%22+label%3A%22Type%3A+bug%22+-label%3A%22Priority%3A+Critical%22+-label%3A%22Priority%3A+Medium%22+-label%3A%22Priority%3A+Blocker%22|[" + str(len(older_untriaged_bugs)) + "]>*" + "\n\n")
    message["to_fix"] += "🐜 *Need fix (%s)* 🐜" % (len(blockers) + len(critical) + len(others)) + "\n"
    message["to_fix"] += "*Blockers (%s)*" % len(blockers) + "\n"
    message["to_fix"] += blockers_message + "\n"
    message["to_fix"] += "*Critical (%s)*" % len(critical) + "\n"
    message["to_fix"] += critical_message + "\n"
    message["to_fix"] += "*Others (%s)*" % len(others) + "\n"
    message["to_fix"] += others_message + "\n"
    message["to_fix"] += "*Triaged bugs older than 2 months: " 
    message["to_fix"] += "<https://github.com/apache/arrow/issues?q=is%3Aissue+is%3Aopen+label%3A%22Component%3A+R%22+label%3A%22Type%3A+bug%22+label%3A%22Priority%3A+Critical%22%2C%22Priority%3A+Medium%22%2C%22Priority%3A+Blocker%22|[" + str(len(older)) + "]>*" + "\n\n"
    message["prs"] += "*🤝 Open PRs (%s)*" % len(prs) + " 🤝 \n"
    message["prs"] += prs_message + "\n"
    return message

def send_message(message, webhook):
    
    for component in ["to_triage", "to_fix", "prs"]:    
        resp = requests.post(webhook, json={            
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message[component]
                    }
                },
                {
                        "type": "divider"
                }
            ]        
        })

        print("\tSLACK ANSWER", resp.content)    

if __name__ == "__main__":
    
    component = "Component: R"
    
    # Get PRs
    prs = get_all_prs()
    open_r_prs = extract_prs(prs, component)
    
    # Get issues
    r_issues = get_all_issues(component)
    bugs = extract_bugs(r_issues)
    
    # Generate and send message
    message = generate_message(bugs, open_r_prs)
    send_message(message, webhook = ZULIP_WEBHOOK)
