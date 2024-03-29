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
        $ rd add day[@time] <reminder text>

        # Mark a reminder as done:
        $ rd done <id_from_`rd`_output>

        # List all upcoming reminders, including
        # those that aren't due yet:
        $ rd ls

    Time and date string formats:

    * MM/DD as month/day
    * @2am, @3pm OR
    * @15, without an am/pm suffix, uses 24-hour time
"""

# Features to add in the future:
# (Maybe this can later be moved to github issues.)
#
# * [ ] Support 7dates.
# * [ ] A snooze command.
# * [ ] Support a +(time) format.
# * [x] The done command ought to print an update str and the new reminders.
# * [ ] Save in a different file completed reminders rather than deleting.
# * [ ] Can delete added reminders that aren't due yet.


# _______________________________________________________________________
# Imports

import json
import os
import sys
import time

from datetime import date, datetime, timedelta


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
        if 'id' in r:
            del r['id']  # This is needed when a reminder was removed.
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

    _reminders = add_ids(reminders)

    # Avoid saving temporary keys like 'id' to disk.
    core_reminders = [
            {'text': r['text'], 'due': r['due']}
            for r in reminders
    ]

    savefile = os.path.expanduser(SAVE_FILE)
    with open(savefile, 'w') as f:
        json.dump(core_reminders, f)

def print_reminders(do_show_all=False):

    reminders = get_reminders()

    # Reminders are kept in order with most-recent first.
    # The most recent reminders may not be due yet, in which
    # case we don't show them.

    now = time.time()
    dbg_print('now:', now)
    num_printed = 0
    for r in reminders:
        dbg_print('r.due:', r['due'])
        if r['due'] > now and not do_show_all:
            continue
        prefix = ('%02d.' % r['id']) if 'id' in r else '--.'
        if do_show_all:
            due_time = datetime.fromtimestamp(r['due'])
            prefix += time.strftime(
                    '  %I:%M %p %m/%d/%Y ',
                    due_time.timetuple()
            )
        print('%s %s' % (prefix, r['text']))
        num_printed += 1

    if num_printed == 0:
        print('No reminders right now!')

def parse_time_str(time_str):
    """ Return the hour indicated by time_str. This currently only understands
        the following syntaxes:

        * 2am   # Returns 2.
        * 5pm   # Returns 17.
        * 15    # Returns 15; no suffix -> interpreted as an hour in [0, 24).
    """

    if time_str.endswith('am'):
        return int(time_str[:-2])
    elif time_str.endswith('pm'):
        return int(time_str[:-2]) + 12
    else:
        return int(time_str)

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

    today = date.today()

    if day_str.startswith('+'):
        day = today + timedelta(days=int(day_str[1:]))

    else:
        day = datetime.strptime(day_str, '%m/%d').date()
        day = day.replace(year=today.year)

    # If `day` is before today, assume it means next year.
    if day < today:

        # If `day` is before today and within the past month, issue a warning.
        # This is a case where the user is likely to have made a mistake.
        if today - timedelta(days=30) < day:
            print('Info: I\'m interpretring %s as indicating next year.' %
                    due_str)
        else:
            dbg_print('Interpreting %s as indicating next year.' % due_str)

        day = day.replace(year=(today.year + 1))

    hour = parse_time_str(time_str)
    if hour is None:
        return None
    due = datetime(day.year, day.month, day.day, hour=hour)

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

    reminders = get_reminders()

    try:
        id_num = int(reminder_id)
    except:
        print('Error: "%s" is not a number.' % reminder_id)
        print_help_and_exit()

    matching = [i for i, r in enumerate(reminders) if r.get('id') == id_num]

    if len(matching) == 0:
        print('Error: no reminder with id "%d."' % id_num)
        print_help_and_exit()

    assert(len(matching) == 1)

    index = matching[0]
    print('Marking as done: %s' % reminders[index]['text'])
    del reminders[index]
    save_reminders(reminders)

    print('\n____________________________')
    print('These remain:\n')
    print_reminders()

def print_help_and_exit():
    print(__doc__)
    sys.exit(2)


# _______________________________________________________________________
# Main

if __name__ == '__main__':

    if len(sys.argv) == 1:
        print_reminders()
    elif sys.argv[1] == 'ls':
        print_reminders(do_show_all=True)
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
