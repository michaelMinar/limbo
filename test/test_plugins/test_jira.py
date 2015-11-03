# -*- coding: UTF-8 -*-
import os
import sys

from nose.tools import eq_
import vcr

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '../../limbo/plugins'))

from jira_tickets import on_message

# The set of valid gifs given the bananas fixture
test_ticket = [u'TD-11123']

def test_gif():
    ret = on_message({"text": u"!TD-11123"}, None)
    assert 'Bertrand Cariou' in ret
