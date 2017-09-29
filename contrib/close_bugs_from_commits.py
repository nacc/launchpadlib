#!/usr/bin/env python

# Copyright (C) 2009 Canonical Ltd.
#
# This file is part of launchpadlib.
#
# launchpadlib is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# launchpadlib is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with launchpadlib. If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import re
import os
import sys
from ConfigParser import RawConfigParser

from bzrlib.branch import Branch

from launchpadlib.launchpad import Launchpad

fixed_bug_freeform_re = re.compile(
    r'\(fixes bugs{0,1} (\d+(?:,\s*\d+)*)\)', re.IGNORECASE)
fixed_bug_structured_re = re.compile(
    r'\[bugs{0,1}[= ](\d+(?:,\s*\d+)*)\]', re.IGNORECASE)


def get_fixed_bug_ids(revision):
    """Try to extract which bugs were fixed by this revision."""
    fixed_bugs = set()
    commit_message = ' '.join(revision.message.split())
    match = fixed_bug_freeform_re.search(commit_message)
    if match is None:
        match = fixed_bug_structured_re.search(commit_message)
    if match is not None:
        fixed_bugs.update(int(bug_id) for bug_id in match.group(1).split(','))
    # TODO: Search revision properties.
    return fixed_bugs


def get_config(config_filepath):
    config_parser = RawConfigParser()
    config_parser.read([config_filepath])
    branches = dict(
        (name, dict(location=location))
        for name, location in config_parser.items('Branch Locations'))
    for name in branches:
        branches[name]['last_revno'] = config_parser.getint(
            'Branch States', name)
    projects = config_parser.get('Project', 'name').split(',')
    return branches, projects


def set_last_revno(config_filepath, branch_name, revno):
    config_parser = RawConfigParser()
    config_parser.read([config_filepath])
    config_parser.set('Branch States', branch_name, revno)
    with open(config_filepath, 'w') as config_file:
        config_parser.write(config_file)


def main():
    launchpad = Launchpad.login_with(os.path.basename(sys.argv[0]),
                                     'production')

    branches, project_names = get_config('close_bugs_from_commits.conf')

    projects_links = []
    for project_name in project_names:
        projects_links.append(launchpad.projects[project_name].self_link)
    for branch_name, branch_info in branches.items():
        branch = Branch.open(branch_info['location'])
        repository = branch.repository
        start_revno = branch_info['last_revno'] + 1
        for revno in range(start_revno, branch.revno()+1):
            rev_id = branch.get_rev_id(revno)
            revision = repository.get_revision(rev_id)
            fixed_bugs = get_fixed_bug_ids(revision)
            for fixed_bug in sorted(fixed_bugs):
                try:
                    lp_bug = launchpad.bugs[int(fixed_bug)]
                except KeyError:
                    # Invalid bug id specified, skip it.
                    continue
                for bug_task in lp_bug.bug_tasks:
                    if bug_task.target.self_link in projects_links:
                        break
                else:
                    # The bug wasn't targeted to our project.
                    continue
                fixed_statuses = [u'Fix Committed', u'Fix Released']
                if bug_task.status not in fixed_statuses:
                    print "Marking bug %s as fixed in r%s." % (
                        lp_bug.id, revno)
                    branch_location = branch_info['location'].replace(
                        'bzr+ssh', 'http')
                    codebrowse_url = (
                        branch_location + '/revision/' + str(revno))
                    bug_task.transitionToStatus(status=u'Fix Committed')
                    bug_task.bug.newMessage(
                        subject=u'Bug fixed by a commit',
                        content=u'Fixed in %s r%s <%s>' % (
                        branch_name, revno, codebrowse_url))
            set_last_revno(
                'close_bugs_from_commits.conf', branch_name, revno)
    return 0



if __name__ == '__main__':
    sys.exit(main())
