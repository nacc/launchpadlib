#!/usr/bin/python
# -*-doctest-*-

"""
    >>> import _pythonpath, lpapi
    >>> lp = lpapi.lp_factory('dev')

    >>> bzr = lp.projects['bzr']
    >>> print bzr.reviewer_whiteboard
    tag:launchpad.net:2008:redacted
    >>> bzr.reviewer_whiteboard = "Check on licensing"
    >>> print bzr.reviewer_whiteboard
    Check on licensing
    >>> bzr.lp_save()
    ...
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> inactive = lp.projects.licensing_search(active=False)
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> active = lp.projects.licensing_search(active=True)
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> projs = lp.projects.licensing_search(license_reviewed=False)
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> projs = lp.projects.licensing_search(has_zero_licenses=True)
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> projs = lp.projects.licensing_search(licenses=['Other/Proprietary'])
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> bzr.licenses
    []

    >>> projs = lp.projects.licensing_search(has_zero_licenses=False)
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> projs = lp.projects.licensing_search(licenses=['GNU Affero GPL v3'])
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> projs = lp.projects.licensing_search(
    ...     subscription_expires_after="2005-01-01")
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

    >>> projs = lp.projects.licensing_search(has_zero_licenses=True,
    ...                                      search_text="Bazaar")
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 401: Unauthorized

"""

if __name__ == '__main__':
    # Remove existing credentials.
    import os
    try:
        os.unlink(os.path.join(os.environ['HOME'], 'dev.auth'))
    except OSError:
        pass

    # Create correct credentials.
    print "Login as 'test@canonical.com' in your browser."
    print "Press <Enter> when done."
    raw_input()

    # Import _pythonpath and the lpapi module.  _pythonpath must
    # precede the import of lpapi as it redefines sys.path.
    import _pythonpath, lpapi
    lp = lpapi.lp_factory('dev')
    import doctest
    doctest.testmod()
