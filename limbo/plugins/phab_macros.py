"""Translate phabricator macro names into unfurl-able URLs"""

from phabricator import Phabricator
import os
import re

PHAB_HOST = os.environ['PHAB_HOST']
PHAB_ENDPOINT = 'https://' + PHAB_HOST
PHAB_API_ENDPOINT = 'https://' + PHAB_HOST + '/api/'
PHAB_API_TOKEN = os.environ['PHAB_API_TOKEN']
PHAB_FILE_ENDPOINT = 'http://' + os.environ['PHAB_FILE_HOST']

phab = Phabricator(host=PHAB_API_ENDPOINT, token=PHAB_API_TOKEN)

def fetch_macro_uris(names):
    """This function fetches macro URIs

    :param list names: phab macro names
    :returns: (*list*) -- uris for each name
    """
    return [m['uri'] for m in phab.macro.query(names=names).values()]

def find_macro_names(text):
    """This function finds macro names in the given text

    :param str text:
    :returns: (*list*) -- list of phab macro names pulled from input string
    """
    return map(lambda name: name.lower(),
               re.findall('(' + '|'.join(phab.macro.query().keys()) + ')', text, re.IGNORECASE))

def on_message(msg, server):
    """This function handles messages"""
    found_macros = find_macro_names(msg.get("text", ""))
    if found_macros:
        return ' '.join(map(lambda uri: re.sub('^' + PHAB_ENDPOINT, PHAB_FILE_ENDPOINT, uri),
                            fetch_macro_uris(found_macros)))
