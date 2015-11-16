"""A plugin to allow us to issue jira queries over slack"""

from jira import JIRA
import os
import re
import datetime

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
        'issue_type': raw['issuetype']['name']
    }


def extract_issue_data(issue):
    """pull out a short description of each issue and return a string"""
    issue_data = preprocess(issue)
    for key in issue_data.keys():
        issue_data[key] = issue_data[key].encode('ascii', 'ignore')
    issue_data['url'] = 'https://trifacta.atlassian.net/browse/{0}'.format(issue.key)
    issue_data['ticket'] = issue.key
    return '{assignee}: {ticket} ({issue_type}) - {summary}\n{url}'.format(**issue_data)


def get_recently_resolved_query(team):
    """Get a list of issues resolved in the last day"""
    if datetime.date.today().weekday() in [6, 0] :
        lag = 3
    else:
        lag = 1
    return '''issuetype in (Bug, "Engineering Story", Story) AND
        status in (Resolved, Closed) and updated >= -{0}d AND
        assignee in membersOf({1}) ORDER BY assignee,
        updated DESC'''.format(lag, team)



def get_in_progress_query(team):
    """Take in a team name and return the jql query for retrieving issues"""
    return '''
        issuetype in (Bug, "Engineering Story", Story) AND
        status = "In Progress" AND resolution = Unresolved AND
        assignee in membersOf({0}) ORDER BY assignee, updated DESC
        '''.format(team)


def run_scrum_query(team):
    """Take a text query and run it against our JIRA corpus"""
    conn = JIRA(OPTIONS, basic_auth=(JIRA_USER, JIRA_AUTH))
    if team == 'serenity':
        jql_team_name = 'Bufs'
    else:
        jql_team_name = team
    recent_resolution_qry = get_recently_resolved_query(jql_team_name)
    in_progress_qry = get_in_progress_query(jql_team_name)
    recent_issues = conn.search_issues(recent_resolution_qry)
    progress_issues = conn.search_issues(in_progress_qry)

    recent_lines = '\n'.join(map(extract_issue_data, recent_issues))
    progress_lines = '\n'.join(map(extract_issue_data, progress_issues))
    msg = ['*Team recently closed/resolved:*', recent_lines,
           '*And folks are currently working on:*', progress_lines]
    return '\n'.join(msg)


def on_message(msg, server):
    text = msg.get("text", "")
    match = re.findall(r"(\w+\s+|\b)rs scrum (.*)", text)
    if not match:
        return

    searchterm = match[0][1]
    return run_scrum_query(searchterm)
