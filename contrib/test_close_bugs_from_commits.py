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

"""Test for close_bugs_from_commits.get_fixed_bug_ids()."""

import unittest

from close_bugs_from_commits import get_fixed_bug_ids


class FakeRevision:

    def __init__(self, message):
        self.message = message


class TestGetFixedBugIds(unittest.TestCase):

    def test_one_freeform(self):
        # One bug specified in the format: (fixes bug 42)
        self.assertEqual(
            get_fixed_bug_ids(FakeRevision("before (fixes bug 42) after")),
            set([42]))

    def test_multiple_freeform(self):
        # Multiple bugs specified in the format: (fixes bugs 42, 84, 168)
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("before (fixes bug 42, 84, 168) after")),
            set([42, 84, 168]))
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("before (fixes bug 42,84,168) after")),
            set([42, 84, 168]))

    def test_freeform_case_insensitve(self):
        # The freeform format isn't case sensitive.
        self.assertEqual(
            get_fixed_bug_ids(FakeRevision("before (FIXES BUG 42) after")),
            set([42]))

    def test_one_structured(self):
        # One bug specified in the format: [bug=42]
        self.assertEqual(
            get_fixed_bug_ids(FakeRevision("before [bug=42]) after")),
            set([42]))

    def test_one_structured_no_equal_sign(self):
        # One bug specified in the format: [bug 42]
        self.assertEqual(
            get_fixed_bug_ids(FakeRevision("before [bug 42]) after")),
            set([42]))

    def test_multiple_structured(self):
        # Multiple bugs specified in the format: [bug=42, 84, 168]
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("before [bug=42, 84, 168]) after")),
            set([42, 84, 168]))

    def test_multiple_structured_bugs(self):
        # Multiple bugs specified in the format: [bugs=42, 84, 168]
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("before [bugs=42, 84, 168]) after")),
            set([42, 84, 168]))
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("before [bugs=42,84,168]) after")),
            set([42, 84, 168]))

    def test_mention_bug(self):
        # Bugs simply mentioned among the commit message shouldn't be
        # considered being fixed.
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("find bug 4231 after")),
            set([]))

    def test_mention_multiple_bugs(self):
        # Bugs simply mentioned among the commit message shouldn't be
        # considered being fixed.
        self.assertEqual(
            get_fixed_bug_ids(
                FakeRevision("find bug 123456 after 2345 and also 1234, end.")),
            set([]))

