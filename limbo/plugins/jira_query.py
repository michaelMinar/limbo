"""A plugin to allow us to issue jira queries over slack"""

from jira import JIRA
import os
import re

JIRA_USER = os.environ['JIRA_USER']
JIRA_AUTH = os.environ['JIRA_AUTH']
OPTIONS = {
    'server': 'https://trifacta.atlassian.net'
}


def preprocess(issue):
    """Takes a single issue pulled from a JIRA query and
    extracts shortend version for more compact posting by rosencrantz
    :returns: (*dict*)
    """
    raw = issue.raw['fields']
    return {
        'summary': raw['summary'],
        'assignee': raw['assignee']['displayName'],
        'status': raw['status']['name'],
    }


def extract_issue_data(issue):
    """pull out a short description of each issue and return a string"""
    issue_data = preprocess(issue)
    for key in issue_data.keys():
        issue_data[key] = issue_data[key].encode('ascii', 'ignore')
    issue_data['url'] = 'https://trifacta.atlassian.net/browse/{0}'.format(issue.key)
    issue_data['ticket'] = issue.key
    return'{ticket}: {summary}, {status}, {assignee}, {url}'.format(**issue_data)


def run_query(qry):
    """Take a text query and run it against our JIRA corpus"""
    conn = JIRA(OPTIONS, basic_auth=(JIRA_USER, JIRA_AUTH))
    issues = conn.search_issues(qry)
    lines = map(extract_issue_data, issues[0:5])
    return '\n'.join(lines)


def on_message(msg, server):
    text = msg.get("text", "")
    match = re.findall(r"(\w+\s+|\b)rs jira (.*)", text)
    if not match:
        return

    searchterm = match[0][1]
    return run_query(searchterm)
