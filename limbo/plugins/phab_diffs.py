"""Attach meta data to phab diffs posted in Slack

Wants these environment variables:
PHAB_HOST      -- the hostname where your phabricator lives
PHAB_API_TOKEN -- a valid api token for some phabricator bot account
PHAB_FILE_HOST -- hostname for instance of https://github.com/emarschner/phabricator-file-proxy
                  configured to point at PHAB_HOST
"""

from phabricator import Phabricator
import itertools
import os
import re

PHAB_HOST = os.environ['PHAB_HOST']
PHAB_ENDPOINT = 'https://' + PHAB_HOST
PHAB_API_ENDPOINT = 'https://' + PHAB_HOST + '/api/'
PHAB_API_TOKEN = os.environ['PHAB_API_TOKEN']
PHAB_FILE_ENDPOINT = 'http://' + os.environ['PHAB_FILE_HOST']

phab = Phabricator(host=PHAB_API_ENDPOINT, token=PHAB_API_TOKEN)

TEMPLATE_STR = 'Test Plan:'

REVIEWERS = {
    'michaelMinar': 'mminar',
    'joe.m': 'joe.mckenney',
    'stephan': 'steps',
    'jaypranavamurthi': 'jay',
    'adam': 'adamsilberstein',
    'nserrino': 'natalie',
    'sraza': 'safder',
    'sesh': 'seshadri',
    'vikram': 'vikramshrowty'
}


def extract_diff_msg(commit):
    """Takes a phabricator commit message and conditionally extracts messages
    which match our template. In this case that means checking for existence of
    a test plan

    :param dict commit:
    :returns (*dict*) or None
    """
    commit_hash, commit_data = commit
    if TEMPLATE_STR in commit_data['message']:
        return commit_data


def extract_all_properties(response):
    """Takes a raw response from our querydiffs and extracts as many 'properties'
    fields as it can from the individual commits

    :param phabricator.Result response:
    :returns: (*list*)
    """
    all_props = []
    for key in response.keys():
        if 'properties' in response[key]:
            all_props.append(response[key]['properties'])
    return filter(lambda y: len(y) > 0 and type(y) == dict, all_props)


def extract_reviewers(msg):
    """Take the plain diff message, parse it and extract the reviewers

    :param str msg:
    :return: (*list*)
    """
    parsd = re.findall(r"(Reviewers:)(.+)(\n)", msg, re.MULTILINE)[0][1]
    names = parsd.replace(' ', '').split(',')
    return map(lambda name: '@' + REVIEWERS.get(name, name), names)

def phab_diff_query(diff_tag, summon):
    """Takes in a differential tag DXXXX and returns meta data

    :param str diff_tag:
    :returns (*dict*)
    """
    raw = phab.differential.querydiffs(revisionIDs=[diff_tag[1:]])
    if raw.response:
        all_props = extract_all_properties(raw)
        local_commits = map(lambda y: y['local:commits'], all_props)
        flattened = reduce(lambda a, b: a + b, map(lambda y: y.items(), local_commits))
        diff_rev = filter(lambda y: y is not None, map(extract_diff_msg, flattened))

        if len(diff_rev) > 0:
            record = diff_rev[0]
            record['diff_tag'] = diff_tag
            return format_line(record, summon)


def format_line(record, summon):
    """Take in the meta data dictionary associated with a differential revision
    and create a printable string

    :param dict record:
    :param bool summon: whether or not to summon reviewers
    """
    record['uri'] = 'https://phab.trifacta.com/{0}'.format(record['diff_tag'])
    if not summon:
        return '{diff_tag}: {author} \n {summary} \n {uri}'.format(**record)
    else:
        record['summon_stmt'] = ', '.join(extract_reviewers(record['message']))
        return '*ping for review:* \n {diff_tag}: {author} \n {summary} \n {uri} \n {summon_stmt}'.format(**record)


def on_message(msg, server):
    """Listen for patterns like D{number} bounded by word boundaries
    """
    text = msg.get("text", "")
    matches = re.findall(r"(\b)(ping |qd )?(D+\d+)", text)
    if not matches:
        return

    resps = map(
        lambda matched: phab_diff_query(matched[2].encode('utf8'), matched[1].encode('utf8')),
        matches)
    filtered_resps = filter(lambda msg: msg is not None, resps)
    if len(filtered_resps) > 0:
        return '\n'.join(filtered_resps)
