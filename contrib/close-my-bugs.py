#!/usr/bin/env python

# Copyright (C) 2009-2013 Canonical Ltd.
#
# Author: Julian Edwards <julian.edwards@canonical.com>
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


"""Mark all your Fix Committed bugs in a project's milestone as Fix Released.

Quite useful at the end of a cycle when you want to avoid the pain of doing
it through the web UI!
"""

import os
import sys

from optparse import OptionParser

from launchpadlib.launchpad import Launchpad
from launchpadlib.uris import service_roots

COMMASPACE = ', '
FIX_COMMITTED = 'Fix Committed'
FIX_RELEASED = 'Fix Released'


def main(args):
    usage = """%s: project milestone\n\n%s""" % (sys.argv[0], __doc__)

    parser = OptionParser(usage=usage)
    parser.add_option(
        '-s', '--system', type='string', default='production', dest='lpsystem',
        help=("The Launchpad system to use.  Must be one of %s" %
              COMMASPACE.join(sorted(service_roots))))
    parser.add_option(
        '-y', '--yes', action='store_true', default=False, dest='force',
        help="Skip yes/no prompting and do it anyway")
    parser.add_option(
        '-f', '--force', action="store_true", default=False, dest='force',
        help='Obsolete synonym for --yes')
    parser.add_option(
        '-n', '--dry-run', action='store_true',
        help='Describe what the script would do without doing it.')
    parser.add_option(
        '-m', '--mine-only', action='store_true', default=False,
        help='Only close bugs assigned to me.')
    parser.add_option(
        '-e', '--series', type='string', dest='series', default=None,
        help='If the bug tasks to close are targeted to a series, specify '
             'it here or Launchpad won\'t find any tasks to close. See '
             'https://bugs.launchpad.net/launchpad/+bug/314432')
    options, args = parser.parse_args(args=args)
    if len(args) != 2:
        parser.print_usage()
        return 1

    project = args[0]
    milestone = args[1]

    launchpad = Launchpad.login_with(os.path.basename(sys.argv[0]),
                                     options.lpsystem)
    lp_project = launchpad.projects[project]
    lp_milestone = lp_project.getMilestone(name=milestone)

    extra_kwargs = {}
    if options.mine_only:
        extra_kwargs['assignee'] = launchpad.me

    if options.series is not None:
        lp_series = lp_project.getSeries(name=options.series)
        search_object = lp_series
    else:
        search_object = lp_project

    committed_tasks = [
        task for task in search_object.searchTasks(
            status=FIX_COMMITTED, omit_targeted=False, milestone=lp_milestone,
            **extra_kwargs)]

    for task in committed_tasks:
        print "Bug #%s: %s" % (task.bug.id, task.bug.title)

    if options.dry_run:
        print '\n*** Nothing changed.  Re-run without --dry-run/-n to commit.'
    else:
        if not options.force:
            answer = raw_input("Mark these bugs as Fix Released?  [y/N]")
            if answer in ("n", "N") or not answer:
                print "Ok, leaving them alone."
                return

        for task in committed_tasks:
            print "Releasing %s" % task.bug.id
            task.status = FIX_RELEASED
            task.lp_save()
        print "Done."

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
