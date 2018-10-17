#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" rd.py

    A simple shell-based reminder system.

    Usage:

        # Print out current reminders:
        $ rd

        1. This is the most recent reminder.
        2. The second-most recent, and so on until:
        9. The ninth. After this we just say:

        (There are N other reminders.)

        # Add a new reminder:
        rd add day[@time] <reminder text>

        # Mark a reminder as done:
        rd done <id_from_`rd`_output>
"""

# Features to add in the future:
# (Maybe this can later be moved to github issues.)
#
# * [ ] Support 7dates.
# * [ ] A snooze command.
# * [ ] Support a +(time) format.


# _______________________________________________________________________
# Imports

import datetime
import json
import os
import sys
import time


# _______________________________________________________________________
# Constants and Globals

DEBUG_MODE = False

SAVE_FILE = '~/.rd'

# This reflects the state of the reminders *on disk* (as most recently
# loaded). It is only changed by calls to get_reminders() or
# save_reminders(). This may contain temporary metatags like 'id' that
# are not saved to disk.
_reminders = None


# _______________________________________________________________________
# Functions

def dbg_print(*args):
    if DEBUG_MODE:
        print(*args)

def add_ids(reminders):
    """ Given a list of reminder objects, add an 'id' key which matches
        the integers the user will see when the reminders are displayed.
        The augmented reminders are returned as well as changed in place.
    """

    now = time.time()
    num_ids_given = 0
    for r in reminders:
        if r['due'] > now:
            continue
        r['id'] = (num_ids_given + 1)
        num_ids_given += 1

    return reminders

def get_reminders():

    global _reminders

    if _reminders is not None:
        return _reminders

    savefile = os.path.expanduser(SAVE_FILE)

    if os.path.isfile(savefile):
        with open(savefile) as f:
            _reminders = add_ids(json.load(f))
        dbg_print('Loaded:')
        dbg_print(_reminders)
    else:
        dbg_print('Looks like ~/.rd isn\'t a file.')
        _reminders = []

    return _reminders

def save_reminders(reminders):

    global _reminders

    _reminders = reminders

    # Avoid saving temporary keys like 'id' to disk.
    core_reminders = [
            {'text': r['text'], 'due': r['due']}
            for r in reminders
    ]

    savefile = os.path.expanduser(SAVE_FILE)
    with open(savefile, 'w') as f:
        json.dump(core_reminders, f)

def print_reminders():

    reminders = get_reminders()

    # Reminders are kept in order with most-recent first.
    # The most recent reminders may not be due yet, in which
    # case we don't show them.

    now = time.time()
    dbg_print('now:', now)
    num_printed = 0
    for r in reminders:
        dbg_print('r.due:', r['due'])
        if r['due'] > now:
            continue
        print('%02d. %s' % (r['id'], r['text']))
        num_printed += 1

    if num_printed == 0:
        print('No reminders right now!')

def parse_due_str(due_str):
    """ Return a time tuple based on the human-written string
        `due_str`. This returns None if the string couldn't be parsed.

        Day strings understood:
        * 12/25

        Time suffixes understood:
        * TBD
    """

    parts = due_str.split('@')

    if len(parts) > 2:
        return None

    day_str = parts[0]
    time_str = parts[1] if len(parts) > 1 else '8am'

    # TODO: By default, interpret cross-year boundaries intuitively.

    date = datetime.datetime.strptime(day_str, '%m/%d').date()
    now  = datetime.datetime.now().date()
    date = date.replace(year=now.year)

    due = datetime.datetime(date.year, date.month, date.day, hour=8)

    return due.timetuple()

def add_reminder(due_str, text):

    due = parse_due_str(due_str)

    if due is None:
        # TODO Make it easier for users to understand the format here.
        print('Unable to parse the due date: %s' % due_str)
        sys.exit(2)

    reminders = get_reminders()
    reminders.append({'text': text, 'due': time.mktime(due)})
    reminders = sorted(reminders, key=lambda x: x['due'], reverse=True)
    save_reminders(reminders)

    print('Added:', text)
    print('Due:', time.strftime('%I:%M %p %A, %B %e, %Y', due).strip())

def mark_done(reminder_id):
    # TODO Implement this.
    pass

def print_help_and_exit():
    print(__doc__)
    sys.exit(2)


# _______________________________________________________________________
# Main

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print_reminders()
    elif sys.argv[1] == 'add':
        if len(sys.argv) < 4:
            print_help_and_exit()
        add_reminder(sys.argv[2], ' '.join(sys.argv[3:]))
    elif sys.argv[1] == 'done':
        if len(sys.argv) < 3:
            print_help_and_exit()
        mark_done(int(sys.argv[2]))
    else:
        print_help_and_exit()
