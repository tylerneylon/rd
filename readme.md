# rd

*A simple bash-based reminder system*

This is something I built because Google Inbox was murdered.

## Installation

I assume that both `python3` and `/usr/local/bin` are in your path.

    git clone https://github.com/tylerneylon/rd.git
    ln -s $(pwd)/rd/rd.py /usr/local/bin/rd

## Usage

```
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
```
