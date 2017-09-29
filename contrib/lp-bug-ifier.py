#!/usr/bin/env python

"""
Scan stdin for text matching bug references and insert the bug title into the
output on stdout.

Note that titles for private bugs are not fetched but instead are marked
(Private).

Example use:
% cat standup-notes.txt | lp-bug-ifier.py > standup-notes-expanded.txt

Required pacakages:
python-launchpadlib

Original author: kiko
"""

import os
import sys
import re

from launchpadlib import errors
from launchpadlib.launchpad import Launchpad


bug_re = re.compile(r"[Bb]ug(?:\s|<br\s*/>)*(?:\#|report|number\.?|num\.?|no\.?)?"
                     "(?:\s|<br\s*/>)*(?P<bugnum>\d+)")

launchpad = Launchpad.login_with(os.path.basename(sys.argv[0]), 'production')
bugs = launchpad.bugs


def add_summary_to_bug(match):
    text = match.group()
    bugnum = match.group("bugnum")
    try:
        bug = bugs[bugnum]
        summary = bug.title
    except errors.HTTPError:
        summary = 'Private'
    return "%s (%s)" % (text, summary)


def main():
    text = sys.stdin.read()
    print bug_re.sub(add_summary_to_bug, text)

if __name__ == '__main__':
    main()
