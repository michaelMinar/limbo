"""Adding jira ticket metadata to a user inputted ticket"""

try:
    from urllib import quote, unquote
except ImportError:
    from urllib.request import quote, unquote
import re
import requests

def jira(searchterm):

    return 'https://trifacta.atlassian.net/browse/TD-{0}'.format(searchterm)

def on_message(msg, server):
    text = msg.get("text", "")
    match = re.findall(r"!TD-([0-9]{5})", text)
    if not match:
        return

    searchterm = match[0]
    return jira(searchterm.encode("utf8"))
