"""Adding jira ticket metadata to a user inputted ticket"""

try:
    from urllib import quote, unquote
except ImportError:
    from urllib.request import quote, unquote
from dateutil import parser
from jira import JIRA
import json
import os
import re
import requests
import sys

JIRA_USER = os.environ['JIRA_USER']
JIRA_AUTH = os.environ['JIRA_AUTH']
OPTIONS = {
    'server': 'https://trifacta.atlassian.net'
}
conn = JIRA(OPTIONS, basic_auth=(JIRA_USER, JIRA_AUTH))
DISPLAY_KEYS = ['summary', 'description', 'status', 'priority',
                'assignee', 'reporter', 'created_at', 'updated']


def extract_repeated_field(array, field_name, merge_fields=True):
    """The structure of JIRA's issues contains arrays of dictionaries. Here
    we have a simple helper to extract a field from each and send back an
    array of those values

    :param list array:
    :param string field_name:
    :returns: (*list*)
    """
    if array is None:
        return None
    vals = map(lambda entry: entry.get(field_name, None), array)
    return_fields = filter(lambda entry: entry is not None, vals)
    if merge_fields:
        return ','.join(return_fields)
    else:
        return return_fields


def preprocess(issue):
    """Takes a single issue pulled from a JIRA query and
    extracts the relevant information. Organizing it into a python
    dict

    :param jira.resource.Issue issue:
    :returns: (*dict*)
    """
    raw = issue.raw['fields']
    if raw.get('customfield_11204', None) is not None:
        bug_cause = raw['customfield_11204']['value']
    else:
        bug_cause = None
    return {
        'id': issue.key,
        'summary': raw['summary'],
        'description': raw['description'],
        'assignee': raw['assignee']['displayName'],
        'components': extract_repeated_field(raw['components'], 'name'),
        'affected_versions': extract_repeated_field(raw['versions'], 'name'),
        'fix_versions': extract_repeated_field(raw['fixVersions'], 'name'),
        'priority': raw['priority']['name'],
        'status': raw['status']['name'],
        'resolution': raw['resolution'],
        'created_at': parser.parse(raw['created']).strftime('%Y-%m-%d'),
        'reporter': raw['reporter']['displayName'],
        'issue_type': raw['issuetype']['name'],
        'architecture_component': extract_repeated_field(raw['customfield_11203'], 'value', False),
        'bug_cause': bug_cause,
        'updated': parser.parse(raw['updated']).strftime('%Y-%m-%d')
    }


def query_ticket(searchterm):

    issue = preprocess(conn.issue('TD-{0}'.format(searchterm)))
    lines = []
    for key in DISPLAY_KEYS:
        issue_data = '{0}: {1}'.format(key, issue.get(key, ''))
        new_line = ' '.join(issue_data.split('\n\r')[0:3])
        lines.append(new_line)
    lines.append('url: https://trifacta.atlassian.net/browse/TD-{0}'.format(searchterm))
    full_msg = '\n'.join(lines)
    return full_msg


def on_message(msg, server):
    text = msg.get("text", "")
    match = re.findall(r"!TD-([0-9]{5})", text)
    if not match:
        return

    searchterm = match[0]
    return query_ticket(searchterm.encode("utf8"))
    #return searchterm
