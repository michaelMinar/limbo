"""Translate phabricator macro names into unfurl-able URLs

Wants these environment variables:
PHAB_HOST      -- the hostname where your phabricator lives
PHAB_API_TOKEN -- a valid api token for some phabricator bot account
PHAB_FILE_HOST -- hostname for instance of https://github.com/emarschner/phabricator-file-proxy
                  configured to point at PHAB_HOST
"""

from phabricator import Phabricator
import os
import re

PHAB_HOST = os.environ['PHAB_HOST']
PHAB_ENDPOINT = 'https://' + PHAB_HOST
PHAB_API_ENDPOINT = 'https://' + PHAB_HOST + '/api/'
PHAB_API_TOKEN = os.environ['PHAB_API_TOKEN']
PHAB_FILE_ENDPOINT = 'http://' + os.environ['PHAB_FILE_HOST']

phab = Phabricator(host=PHAB_API_ENDPOINT, token=PHAB_API_TOKEN)

CUSTOM_MAP = {
    'nerd rage': 'nerdrage',
    "because we're smart": 'because-we-are-smart',
    'deal breaker': 'dealbreaker',
    '#shutitdown': 'dealbreaker',
    '#champion': 'iwillbeyourchampion',
    'killing it': 'killing-it',
    'what is happening': 'spaceballs-tape',
    'treat yo self': 'treatyoself',
    'treat yourself': 'treatyoself',
    "you're a wizard": 'youre-a-wizard'
}

def find_macro_names(text):
    """Message text comes in, macro names get fetched, and the ones that match go out as a list

    :param str text:
    :returns: (*list*) -- list of phab macro names pulled from input string
    """
    wb = r'(\w+\s+|\b|\W|^)'  # "Word Boundary"

    macro_keys = phab.macro.query().keys()
    complete_keys = macro_keys + CUSTOM_MAP.keys()
    names = r'(' + r'|'.join(complete_keys) + r')'

    return map(lambda name: (name[2] or name[4]).lower(),
               re.findall(r'(' + wb + names + wb + r'|^[\s]*' + names + r'\s*$)',
                          text, re.IGNORECASE | re.MULTILINE))


def fetch_macro_uris(names):
    """"Macro names come in, get fetched from phab, and a list of their URI strings go out

    :param list names: phab macro names
    :returns: (*list*) -- uris for each name
    """
    proper_names = map(swap_back_to_proper_name, names)
    return [m['uri'] for m in phab.macro.query(names=proper_names).values()]

def swap_back_to_proper_name(found_name):
    """Takes a found name and checks if it was a custom map. If found there,
    we swap back the proper phab macro name. Else we just return the found name.

    :param str found_name:
    :returns: (*str*)
    """
    if found_name in CUSTOM_MAP.keys():
        return CUSTOM_MAP[found_name]
    else:
        return found_name

def on_message(msg, server):
    """Macro URIs from message get rewritten for the file proxy and returned separated by newlines

    :param dict msg: slack message data, with body of message as value for the text key
    :returns: str -- newline separated uris pointing at phabricator file proxy service
    """
    found_macros = find_macro_names(msg.get("text", ""))
    if found_macros:
        return '\n'.join(map(lambda uri: re.sub('^' + PHAB_ENDPOINT, PHAB_FILE_ENDPOINT, uri),
                             fetch_macro_uris(found_macros)))
