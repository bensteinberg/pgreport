import json
import humanize


class Report:
    def __init__(self, title, author, release_date,
                 filename, number, corrections):
        self.title = title
        self.author = author
        self.release_date = release_date
        self.filename = filename
        self.number = number
        self.corrections = corrections

    def get_json(self):
        return json.dumps(self, default=vars)

    def __str__(self):
        s = '' if len(self.corrections) == 1 else 's'
        count = humanize.apnumber(len(self.corrections))
        msg = f"""Hi, I’ve been proofing {self.title} and found {count} error{s}:

Title: {self.title}, by {self.author}
Release Date: {self.release_date} [EBook #{self.number}]

File: {self.filename}"""  # noqa
        for c in self.corrections:
            msg += str(c)
        return msg


class Correction:
    """
    The problem here is that lines in SE XHTML are different from the
    lines in PG plain text; the former are whole paragraphs.
    """
    def __init__(self, change, text):
        self.before = change[0]
        self.after = change[1]

        # get the start and end indices of the actual change
        self.start = get_index(self.before, self.after)
        backwards_idx = get_index(self.before, self.after, rev=True)
        self.before_end = len(self.before) - backwards_idx
        self.after_end = len(self.after) - backwards_idx

        # get the bounds of the largest match including the
        # actual change
        actual = ' '.join(self.before[self.start:self.before_end])
        (self.x, self.y) = sorted([
            (x, y)
            for x in range(self.start + 1)
            for y in range(self.start, len(self.before) + 1)
            if ' '.join(self.before[x:y]) in text
            and actual in ' '.join(self.before[x:y])
        ], key=lambda tup: tup[1] - tup[0])[-1]
        self.match = ' '.join(self.before[self.x:self.y])

        # get the line number of the match
        (self.idx, self.orig) = [
            (i + 1, j) for i, j
            in enumerate(text.split('\r\n'))
            if self.match in j
        ][0]

    def __str__(self):
        before = ' '.join(self.before[self.start:self.before_end])
        after = ' '.join(self.after[self.start:self.after_end])
        correction = f'{before} ==> {after}'  # noqa
        return f"""

Line {self.idx}:
{self.orig}
{correction}"""


def get_index(before, after, rev=False):
    """
    Get index of first (or last) difference
    """
    if rev:
        before = before[::-1]
        after = after[::-1]
    return [
        before[i] != after[i]
        for i in range(min(len(before), len(after)))
    ].index(True)
