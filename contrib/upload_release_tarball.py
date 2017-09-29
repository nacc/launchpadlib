#!/usr/bin/python
#
# This script uploads a tarball as a file for a (possibly new)
# release. It takes these command-line arguments:
#
#  PROJECT_NAME SERIES_NAME VERSION TARBALL_PATH [SERVICE_ROOT]
# for instance:
#  lazr.restful pre-1.0 0.9 ./lazr.restfulclient-0.9.tar.gz
# or:
#  foo 1.x 1.5 ./foo-1.5.tar.gz staging
#
# The project and series must exist, because you can't create projects
# or series through the web service. A milestone named after the
# version number will be created if it none exists.
#
# To upload a GPG signature file for the tarball, generate a signature
# file like so:
#  gpg --armor --sign --detach-sig [filename]
#
# The signature will be stored in [filename].asc, which is where this
# script looks.

from datetime import datetime
from optparse import OptionParser
import os
import pytz
import sys

from launchpadlib.launchpad import Launchpad
from launchpadlib.errors import HTTPError


TARBALL_CONTENT_TYPE = 'application/x-tgz'
USAGE = ("%prog [-f|--force] PROJECT_NAME SERIES_NAME VERSION "
         "TARBALL_PATH [SERVICE_ROOT]")

parser = OptionParser(usage=USAGE)
parser.add_option("-f", "--force", action="store_true", dest="force",
                  default=False,
                  help="Submit tarball even if GPG signature file is missing.")
options, args = parser.parse_args()
# Gather the command-line arguments.
if len(args) < 4:
    parser.error("Not enough command-line arguments.")
if len(args) > 5:
    parser.error("Too many command-line arguments.")

project_name, series_name, version_name, tarball_path = args[:4]
if len(args) == 5:
    service_root = sys.argv[-1]
else:
    service_root = 'production'

# Obtain the GPG signature.
release_tarball = open(tarball_path).read()
tarball_name = os.path.split(tarball_path)[1]
signature_path = tarball_path + '.asc'
if os.path.exists(signature_path):
    signature_name = os.path.split(signature_path)[1]
    signature = open(signature_path).read()
else:
    # There is no signature.
    if options.force:
        print ('WARNING: Signature file "%s" is not present. Continuing '
               'without it.' % signature_path)
        signature_name = None
        signature = None
    else:
        print 'ERROR: Signature file "%s" is not present.' % signature_path
        print 'Run "gpg --armor --sign --detach-sig" on the tarball.'
        print 'Or re-run this script with the --force option.'
        sys.exit(-1)

# Now we interact with Launchpad.
launchpad = Launchpad.login_with('Release creation script', service_root)

# Find the project.
try:
    project = launchpad.projects[project_name]
except KeyError:
    raise ValueError('No such project: "%s"' % project_name)
matching_series = [series for series in project.series
                   if series.name == series_name]

# Find the series in the project.
if len(matching_series) == 0:
    raise ValueError('No such series "%s" for project %s' % (
            series_name, project.name))
series = matching_series[0]

# Find the milestone in the series.
matching_milestones = [milestone for milestone in series.active_milestones
                       if milestone.name == version_name]
if len(matching_milestones) == 0:
    print 'No milestone "%s" for %s/%s. Creating it.' % (
        version_name, project.name, series.name)
    milestone = series.newMilestone(name=version_name)
else:
    milestone = matching_milestones[0]

# Find the release in the series.
matching_releases = [release for release in series.releases
                     if release.version == version_name]
if len(matching_releases) == 0:
    # The release doesn't exist already. Create it.
    #
    # The changelog and release notes could go into this operation
    # invocation.
    print "No release for %s/%s/%s. Creating it." % (
        project.name, series.name, version_name)
    release = milestone.createProductRelease(
        date_released=datetime.now(pytz.UTC))
else:
    release = matching_releases[0]

# Upload the file.
kwargs = { 'file_content': release_tarball,
           'content_type': TARBALL_CONTENT_TYPE,
           'file_type': "Code Release Tarball",
           'filename': tarball_name }
if signature is not None:
    kwargs['signature_content'] = signature
    kwargs['signature_filename'] = signature_name
result = release.add_file(**kwargs)

# We know this succeeded because add_file didn't raise an exception.
print "Success!"
print result.self_link
