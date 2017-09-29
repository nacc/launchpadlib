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
from ConfigParser import RawConfigParser
from datetime import date, timedelta
import os
import sys

from bzrlib.branch import Branch

from close_bugs_from_commits import get_fixed_bug_ids
from editmoin import editshortcut
from launchpadlib.launchpad import Launchpad


class Config:
    def __init__(self):
        self.tag_to_story_name = {}
        self.milestone_name = None
        self.start = None
        self.end = None
        self.project_name = None
        self.template_filename = None
        self.branch_location = None
        self.branch_start_revno = None
        self.base_wiki_location = None
        self.stories_page = None

    @property
    def story_tags(self):
        return self.tag_to_story_name.keys()


def get_assignee_name(bugtask):
    """Get the name of the person assigned to the bug task.

    Instead of accessing bugtask.assignee.name, the name is extracted
    from the assignee_link, which avoids fetching the assignee object
    from the web service.
    """
    if bugtask.assignee_link is None:
        return None
    url_parts = bugtask.assignee_link.split('/')
    return url_parts[-1].lstrip('~')


def string_isodate_to_date(string_isodate):
    if 'T' in string_isodate:
        string_isodate, rest = string_isodate.split('T', 1)
    year, month, day = string_isodate.split('-')
    return date(int(year), int(month), int(day))


class MilestoneState:
    """The current state of the milestone."""

    def __init__(self, start, end, today):
        self.days = {}
        self.today = today
        self.start = start
        self.end = end
        one_day = timedelta(days=1)
        current_day = start
        while current_day <= end:
            self.days[current_day] = {}
            current_day += one_day

    def mark_done(self, bug_id, day):
        if day < self.start:
            day = self.start
        if day > self.end:
            # It was fixed after the milestone ended.
            return
        self.days[day][bug_id] = 'D'

    def mark_started(self, bug_id, day):
        if day not in self.days:
            day = self.start
        self.days[day][bug_id] = 'P'

    def mark_added(self, bug_id, day):
        self.days[day][bug_id] = 'N'


def get_config(config_filepath):
    """Create a map between committers and their test pages.

    Read the config file, and return a map, mapping a committer to the
    name of the wiki page where test plans are held.
    """
    config_parser = RawConfigParser()
    config_parser.read([config_filepath])
    config = Config()

    config.branch_location = config_parser.get('Branch', 'location')
    config.branch_start_revno = config_parser.getint('Branch', 'start_revno')

    config.milestone_name = config_parser.get('Milestone', 'name')
    config.project_name = config_parser.get('Milestone', 'project')
    config.template_filename = config_parser.get('Milestone', 'template')
    config.base_wiki_location = config_parser.get(
        'Milestone', 'base_wiki_location')
    config.stories_page = config_parser.get(
        'Milestone', 'stories_page')
    config.start = string_isodate_to_date(
        config_parser.get('Milestone', 'start'))
    config.end = string_isodate_to_date(
        config_parser.get('Milestone', 'end'))
    config.release_critical = string_isodate_to_date(
        config_parser.get('Milestone', 'release_critical'))
    config.story_tags = []
    for tag_name, story_name in config_parser.items('Stories'):
        config.story_tags.append(tag_name)
        config.tag_to_story_name[unicode(tag_name)] = story_name
    return config


class Story:

    def __init__(self, name, tag_name):
        self.name = name
        self.tag_name = tag_name
        self.tasks = []


ALL_BUG_STATUSES = [
    "New",
    "Incomplete",
    "Invalid",
    "Won't Fix",
    "Confirmed",
    "Triaged",
    "In Progress",
    "Fix Committed",
    "Fix Released",
    ]

content_color = {
    'P': '#FF8080',
    'N': '#FFFFE0',
    'D': '#80FF80',
    }

def get_cell_style(content, fallback_color=None):
    color = content_color.get(content, fallback_color)
    if color is not None:
        return '<style="background-color: %s;">' % color
    else:
        return ''

def generate_milestone_table(milestone_state, stories, config):
    table_rows = []
    row_items = [
        "''Story/Task''",
        "''Assignee''",
        ]
    for day in sorted(milestone_state.days.keys()):
        row_items.append("''%s''" % str(day.day))
    table_rows.append('|| %s ||' % ' || '.join(row_items))
    for story in stories:
        row_items = []
        unimportant, story_anchor = story.tag_name.split('-', 1)
        if story.tag_name == 'unrelated-bugs':
            row_items.append(
                '<rowstyle="background-color: #CC6633;">'
                ' %s' % story.name)
        else:
            row_items.append(
                '<rowstyle="background-color: #E0E0FF;">'
                " '''[[%s#%s|%s]]'''" % (
                    config.stories_page, story_anchor, story.name))

        row_items.append('') # Assignee
        task_state = ''
        for day in sorted(milestone_state.days.keys()):
            row_items.append(task_state)
        table_rows.append('||%s ||' % ' ||'.join(row_items))
        for bugtask in story.tasks:
            row_items = []
            row_items.append(
                '[[https://launchpad.net/bugs/%(bug_id)s|#%(bug_id)s]]:'
                ' %(title)s' % dict(
                    bug_id=bugtask.bug.id, title=bugtask.bug.title))
            assignee_name = get_assignee_name(bugtask)
            if assignee_name is not None:
                row_items.append(" [[/%s|%s]] "% (
                    assignee_name, assignee_name))
            else:
                row_items.append('') # Assignee
            task_state = ''
            future_color = ''
            for day, changes in sorted(milestone_state.days.items()):
                task_state = changes.get(bugtask.bug.id, task_state)
                if day > milestone_state.today:
                    task_state = ''
                    if day > config.release_critical:
                        future_color = '#C8BBBE'
                row_items.append("%s %s" % (
                    get_cell_style(task_state, future_color), task_state))
            table_rows.append('|| %s ||' % ' ||'.join(row_items))

    return '\n'.join(table_rows)



def get_day_added(task, fallback=None):
    return fallback


def get_day_started(task):
    if task.date_in_progress is not None:
        return string_isodate_to_date(task.date_in_progress)
    return None


def get_day_done(task):
    # We should be able to use date_closed, but it seems like it's not
    # always set.
    closed_date_attributes = ['date_fix_committed', 'date_fix_released']
    for closed_date_attribute in closed_date_attributes:
        date_closed = getattr(task, closed_date_attribute)
        if date_closed is not None:
            return string_isodate_to_date(date_closed)
    return None


def get_associated_story_tags(bugtask):
    return [tag for tag in bugtask.bug.tags if tag.startswith('story-')]


def main():
    config = get_config('update-milestone-progress.conf')
    launchpad = Launchpad.login_with(os.path.basename(sys.argv[0]),
                                     'production')
    stories = dict(
        (story_tag, Story(story_name, story_tag))
        for story_tag, story_name in sorted(config.tag_to_story_name.items()))
    # 'unrelated' isn't quite right, but I want to sort on the tag name
    # and have the bugs come last.
    stories['unrelated-bugs'] = Story(
        'Bugs not related to a story', 'unrelated-bugs')
    project = launchpad.projects[config.project_name]
    for milestone in project.all_milestones:
        if milestone.name == config.milestone_name:
            break
    else:
        raise AssertionError("No milestone: %s" % config.milestone_name)

    today = date.today()
    milestone_state = MilestoneState(config.start, config.end, today)

    milestone_bugtasks = dict(
        (bugtask.bug.id, bugtask)
        for bugtask in project.searchTasks(status=ALL_BUG_STATUSES,
                                           milestone=milestone))
    assignees = set()
    for task in milestone_bugtasks.values():
        assignee_name = get_assignee_name(task)
        if assignee_name is not None:
            assignees.add(assignee_name)
        associated_story_tags = get_associated_story_tags(task)
        if len(associated_story_tags) == 0:
            # This bug isn't part of a story. Put it into the pseudo
            # story which is used for all such bug fixes.
            associated_story_tags = ['unrelated-bugs']
        for story_tag in associated_story_tags:
            if story_tag not in stories:
                stories[story_tag] = Story(
                    story_tag[len('story-'):], story_tag)
            stories[story_tag].tasks.append(task)
        milestone_state.mark_added(
            task.bug.id, get_day_added(task, fallback=config.start))
        day_started = get_day_started(task)
        if day_started is not None:
            milestone_state.mark_started(task.bug.id, day_started)
        day_done = get_day_done(task)
        if day_done is not None:
            milestone_state.mark_done(task.bug.id, day_done)

    # Look through commits and marks tasks as done, if any bug fixes are
    # found.
    branch = Branch.open(config.branch_location)
    repository = branch.repository
    start_revno = config.branch_start_revno
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
            if milestone_bugtasks.get(lp_bug.id) is not None:
                milestone_state.mark_done(
                    lp_bug.id, date.fromtimestamp(revision.timestamp))

    # Order by the order in the config file first.
    sorted_stories = [stories[story_tag] for story_tag in config.story_tags]
    sorted_stories.extend(
        story for story_tag, story in sorted(stories.items())
        if story_tag not in config.story_tags)
    table = generate_milestone_table(milestone_state, sorted_stories, config)
    with open(config.template_filename, 'r') as template:
        page = template.read() % dict(
            milestone=config.milestone_name,
            progress_table=table,
            )
    def update_if_modified(moinfile):
        if moinfile._unescape(moinfile.body) == page:
            # Nothing has changed, cancel the edit.
            return 0
        else:
            moinfile.body = page
            return 1

    page_shortcut = config.base_wiki_location + config.milestone_name
    editshortcut(page_shortcut, editfile_func=update_if_modified)

    # Generate assignee pages.
    for assignee_name in assignees:
        print "Assignee: %s" % assignee_name
        assignee_stories = dict()
        for story in stories.values():
            assigned_bugs = [
                bug_task for bug_task in story.tasks
                if (bug_task.assignee is not None and
                    bug_task.assignee.name == assignee_name)]
            if len(assigned_bugs) > 0:
                assignee_stories[story.tag_name] = Story(
                    story.name, story.tag_name)
                assignee_stories[story.tag_name].tasks = assigned_bugs
        page = generate_milestone_table(
            milestone_state, assignee_stories.values(), config)
        assignee_page_shortcut = page_shortcut + '/' + assignee_name
        editshortcut(
            assignee_page_shortcut, editfile_func=update_if_modified)

    print "done."

if __name__ == '__main__':
    main()
