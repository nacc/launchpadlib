#!/usr/bin/python

__metaclass__ = type

from collections import defaultdict
from optparse import OptionParser
import sys

from launchpadlib.errors import Unauthorized
from launchpadlib.launchpad import Launchpad


DISTRO_TYPES = (
    'distro_series',
    'distribution_source_package',
    'source_package',
    )
UNSUPPORTED_SPLIT_TYPES = (
    'distro_series',
    'product_series',
    'source_package',
    )


class PublicBugError(ValueError):
    """The bug is public, it is not a privacy concern."""


class SinglePillarError(ValueError):
    """The bug affects one pillar, it is not compromised."""


class UnsupportedSeriesSplit(ValueError):
    """The series bugtasks cannot be split."""


class SharedBugsFixer:

    def __init__(self, options):
        self.verbose = options.verbose
        self.force = options.force
        self.website = options.website

    def log(self, message, leader='    ', error=False):
        """Report to STDOUT."""
        if error or self.verbose:
            print '%s%s' % (leader, message)

    def _get_target_type(self, bug_target):
        """Return the bug target entity type."""
        return repr(bug_target).split(' ')[0][1:]

    def _get_pillar_bugs(self, bug):
        """Build a dict of pillars_names to locate the bugtask."""
        if not bug.private and not self.force:
            raise PublicBugError()
        bugtasks = bug.bug_tasks
        pillars = {}
        pillar_bugs = defaultdict(list)
        for bugtask in bugtasks:
            pillar = bugtask.target
            target_type = self._get_target_type(pillar)
            if target_type == 'project_series':
                pillar = pillar.project
            if target_type in DISTRO_TYPES:
                pillar = pillar.distribution
            name = pillar.name
            pillars[name] = pillar
            pillar_bugs[name].append(bugtask)
        if len(pillars.keys()) == 1:
            raise SinglePillarError()
        return pillars, pillar_bugs

    def delete_bugtask(self, bug_id, pillar_name, split=False):
        """Delete the bug's bugtasks that affect a pillar.

        If split is True, a new bug will be created for the bugtask.
        """
        if split:
            action = 'Splitting'
        else:
            action = 'Deleting'
        self.log(
            "%s %s from bug %s" % (action, pillar_name, bug_id), leader='')
        lp = Launchpad.login_with(
            'delete_bugtasks', service_root=self.website, version='devel')
        try:
            bug = lp.bugs[bug_id]
            pillars, pillar_bugs = self._get_pillar_bugs(bug)
            pillar_names = pillars.keys()
            self.log(
                "bug affects %s pillars: %s" % (
                len(pillar_names), pillar_names))
            # Look for deletable bugtasks for the pillar.
            for bugtask in pillar_bugs[pillar_name]:
                if split:
                    self.split_bugtask(lp, bug, bugtask, pillar_name)
                # Delete the bugtask, this cannot be undone.
                self.log(
                    "deleting %s bugtask for %s." % (pillar_name, bug_id))
                bugtask.lp_delete()
        except PublicBugError:
            self.log("! bug now public. Use force to change this bug.")
        except SinglePillarError:
            self.log("! bug affects 1 pillar now.")
        except UnsupportedSeriesSplit:
            self.log("! This script cannot split bugs that affect series.")
        except (KeyError, Unauthorized), e:
            self.log("! bug %s is owned by someone else" % pillar_name)
        except Exception, e:
            # Something went very wrong.
            self.log("!! %s" % str(e), error=True)

    def split_bugtask(self, lp, bug, bugtask, pillar_name):
        """Create a new bug for a bugtask.

        The new bug will have the same data as the old bug and the old
        bugtask's data will be copied to the new bugtask.
        """
        if self._get_target_type(bugtask.target) in UNSUPPORTED_SPLIT_TYPES:
            raise UnsupportedSeriesSplit()
        new_bug = lp.bugs.createBug(
            target=bugtask.target,
            title=bug.title,
            description='%s\n\nbugdep depends-on bug %s' % (
                (bug.description, bug.id)),
            private=bug.private,
            security_related=bug.security_related,
            tags=bug.tags)
        self.log("Created bug %s" % new_bug.id)
        new_bugtask = new_bug.bug_tasks[0]
        new_bugtask.importance = bugtask.importance
        new_bugtask.bug_watch = bugtask.bug_watch
        new_bugtask.lp_save()
        try:
            new_bugtask.status = bugtask.status
            new_bugtask.lp_save()
        except Unauthorized:
            # Fall back to confirmed.
            new_bugtask.status = 'Confirmed'
            new_bugtask.lp_save()
            self.log("Status set to confirmed instead of Triaged.")
            self.log(
                "You do not have permission to supervise %s bugs." %
                pillar_name)
        try:
            new_bugtask.assignee = bugtask.assignee
            new_bugtask.milestone = bugtask.milestone
            new_bugtask.lp_save()
        except Unauthorized:
            self.log("Could not copy milestone and assignee.")
            self.log(
                "You do not have permission to supervise %s bugs." %
                pillar_name)
        # Update original bug.
        bug.description = '%s\n\nbugdep dependent bug %s' % (
            (bug.description, new_bug.id))
        bug.lp_save()


def get_option_parser():
    """Return the option parser for this program."""
    usage = "%prog [options] bug_id:project_name [bug_id:project_name]"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-v", "--verbose", action="store_true", dest="verbose")
    parser.add_option(
        "-q", "--quiet", action="store_false", dest="verbose")
    parser.add_option(
        "-f", "--force", action="store_true", dest="force",
        help="Delete or split bug tasks that belong to a public bug")
    parser.add_option(
        "-d", "--delete", action="store_true", dest="deletable",
        help="Delete a spurious project bug task from a bug")
    parser.add_option(
        "-s", "--split", action="store_true", dest="splitable",
        help=("Split a project bug task from an existing bug "
              "so that the issue can be tracked separately"))
    parser.add_option(
        "-w", "--website", dest="website",
        help=("The URI of Launchpad web site.                               "
              "Default: https://api.launchpad.net;                          "
              "Alternates: https://api.staging.launchpad.net, "
              "https://api.qastating.launchpad.net"))
    parser.set_defaults(
        verbose=True,
        force=False,
        deletable=False,
        splitable=False,
        website='https://api.launchpad.net',
        )
    return parser


def main(argv=None):
    """Run the command line operations."""
    if argv is None:
        argv = sys.argv
    parser = get_option_parser()
    (options, args) = parser.parse_args(args=argv[1:])
    if (not (options.deletable or options.splitable)
        or options.deletable and options.splitable):
        parser.error("You must specify delete or split.")
    if len(args) == 0:
        parser.error("bug_id:project_name not specified.")
    pairs = []
    for pair in args:
        if ':' not in pair:
            parser.error("Could not parse: bug_id:project_name")
        pairs.append(pair.split(':'))
        try:
            int(pairs[-1][0])
        except ValueError:
            parser.error("bug_id is not a number.")
    summariser = SharedBugsFixer(options)
    for bug_id, project_name in pairs:
        summariser.delete_bugtask(
            bug_id, project_name, split=options.splitable)


if __name__ == '__main__':
    sys.exit(main())
