#!/usr/bin/python
# -*-doctest-*-

"""
    >>> import _pythonpath, lpapi
    >>> lp = lpapi.lp_factory('dev')
    >>> bzr = lp.projects['bzr']
    >>> bzr.reviewer_whiteboard = "Check on licensing"
    >>> print bzr.reviewer_whiteboard
    Check on licensing
    >>> bzr.lp_save()
    >>> print bzr.reviewer_whiteboard
    Check on licensing

    >>> from operator import attrgetter
    >>> def print_projs(projs):
    ...     for p in sorted(projs, key=attrgetter('name')):
    ...         print p.name

    >>> inactive = lp.projects.licensing_search(active=False)
    >>> print_projs(inactive)
    python-gnome2-dev
    unassigned

    >>> active = lp.projects.licensing_search(active=True)
    >>> print_projs(active)
    a52dec
    alsa-utils
    applets
    aptoncd
    arch-mirrors
    bazaar
    bzr
    derby
    evolution
    firefox
    gnome-terminal
    gnomebaker
    iso-codes
    jokosher
    landscape
    launchpad
    mega-money-maker
    netapplet
    redfish
    rosetta
    thunderbird
    tomcat
    upstart


    >>> projs = lp.projects.licensing_search(license_reviewed=False)
    >>> print_projs(projs)
    a52dec
    applets
    aptoncd
    arch-mirrors
    bazaar
    bzr
    derby
    evolution
    firefox
    gnome-terminal
    gnomebaker
    iso-codes
    jokosher
    landscape
    launchpad
    mega-money-maker
    netapplet
    redfish
    thunderbird
    tomcat
    upstart

    >>> projs = lp.projects.licensing_search(has_zero_licenses=True)
    >>> print_projs(projs)
    a52dec
    alsa-utils
    applets
    aptoncd
    arch-mirrors
    bazaar
    bzr
    evolution
    firefox
    gnome-terminal
    gnomebaker
    iso-codes
    jokosher
    landscape
    launchpad
    netapplet
    python-gnome2-dev
    redfish
    rosetta
    thunderbird
    unassigned
    upstart

    >>> projs = lp.projects.licensing_search(licenses=['Other/Proprietary'])
    >>> print_projs(projs)
    mega-money-maker

    >>> bzr.licenses
    []

    >>> projs = lp.projects.licensing_search(has_zero_licenses=False)
    >>> print_projs(projs)
    derby
    mega-money-maker
    tomcat

    >>> projs[0].licenses
    [u'Apache License']
    >>> projs[1].licenses
    [u'Other/Proprietary']
    >>> projs[2].licenses
    [u'Academic Free License', u'GNU Affero GPL v3']

    >>> projs = lp.projects.licensing_search(licenses=['GNU Affero GPL v3'])
    >>> print_projs(projs)
    tomcat

    >>> projs = lp.projects.licensing_search(
    ...     subscription_expires_after="2005-01-01")
    >>> print_projs(projs)
    >>> projs = lp.projects.licensing_search(has_zero_licenses=True,
    ...                                      search_text="Bazaar")
    >>> print_projs(projs)
    bazaar
    bzr
    launchpad

    >>> l = projs[2]
    >>> print l.name
    launchpad
    >>> print l.description
    Launchpad's design is inspired by the Description of a Project (DOAP) framework by Edd Dumbill, with extensions for actual releases of products.
    >>> print l.summary
    Launchpad is a catalogue of libre software projects and products. Projects registered in the Launchpad are linked to their translations in Rosetta, their bugs in Malone, their RCS imports in Bazaar, and their packages in Soyuz.

"""

if __name__ == '__main__':
    # Remove existing credentials.
    import os
    try:
        os.unlink(os.path.join(os.environ['HOME'], 'dev.auth'))
    except OSError:
        pass

    # Create correct credentials.
    print "Login as 'commercial-member@canonical.com' in your browser."
    print "Press <Enter> when done."
    raw_input()

    # Import _pythonpath and the lpapi module.  _pythonpath must
    # precede the import of lpapi as it redefines sys.path.
    import _pythonpath, lpapi
    lp = lpapi.lp_factory('dev')

    import doctest
    doctest.testmod()
