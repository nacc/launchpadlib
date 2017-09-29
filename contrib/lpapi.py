#!/usr/bin/python2.4
import os
import sys
from urlparse import urljoin
import commands

try:
    from launchpadlib.launchpad import (
        Launchpad, STAGING_SERVICE_ROOT)
    from launchpadlib.credentials import Credentials
    from launchpadlib.errors import *
    import launchpadlib
except ImportError:
    print >> sys.stderr, "Usage:"
    print >> sys.stderr, "   PYTHONPATH=somebranch/lib %s" % sys.argv[0]
    raise


class InvalidCredentials(Exception):
    """Exception for invalid credentials."""
    pass


class LPSystem:
    """Launchpad system class.

    Handles retrieving credentials and connecting to the appropriate API
    endpoint.
    """
    endpoint = None
    auth_file = None
    def __init__(self, app_name='just testing', use_cache=True):
        home = os.environ['HOME']
        if use_cache:
            cache_dir = os.path.join(home, '.launchpadlib', 'cache')
            if not os.path.exists(cache_dir):
                cache_dir = None
        else:
            cache_dir = None
        try:
            # Load credentials from AUTH_FILE if it exists.
            self.auth_file = os.path.join(home, self.auth_file_name)
            self.credentials = Credentials()
            self.credentials.load(open(self.auth_file))
            print >> sys.stderr, "Loading credentials..."
            try:
                self.launchpad = Launchpad(self.credentials, self.endpoint,
                                           cache=cache_dir)
            except launchpadlib.errors.HTTPError:
                raise InvalidCredentials, (
                    "Please remove %s and rerun %s to authenticate." % (
                    self.auth_file, sys.argv[0]))
        except IOError:
            # Prompt for authentication process, then save credentials to
            # AUTH_FILE.
            try:
                self.launchpad = Launchpad.get_token_and_login(app_name,
                                                               self.endpoint,
                                                               cache=cache_dir)
                self.launchpad.credentials.save(open(self.auth_file, "w"))
                print >> sys.stderr, "Credentials saved"
            except launchpadlib.errors.HTTPError, err:
                print >> sys.stderr, err.content
                raise

    @property
    def url(self):
        return urljoin(self.endpoint, 'projects/')


class Staging(LPSystem):
    """Connection to staging."""
    endpoint = STAGING_SERVICE_ROOT
    auth_file_name = 'staging.auth'


class Production(LPSystem):
    """Connection to production."""
    endpoint = 'https://api.launchpad.net/beta/'
    auth_file_name = 'production.auth'


class Dev(LPSystem):
    """Connection to local development version of Launchpad."""
    endpoint = 'https://api.launchpad.dev/beta/'
    auth_file_name = 'dev.auth'
    def __init__(self, app_name='just testing'):
        LPSystem.__init__(self, app_name=app_name, use_cache=False)


systems = dict(dev=Dev,
               staging=Staging,
               production=Production,
               prod=Production,
               )


def lp_factory(system_name, app_name='just_testing'):
    """Get a launchpad API instance for ``system_name``."""
    try:
        system_name = system_name.lower()
        lpinstance = systems[system_name]
        return lpinstance(app_name).launchpad
    except KeyError:
        print >> sys.stderr, "System '%s' not supported." % system_name
        print >> sys.stderr, "Use one of: ", systems.keys()
        return None
