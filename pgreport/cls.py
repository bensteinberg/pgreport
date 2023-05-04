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
    def __init__(self, change, text):
        self.before = change[0]
        self.after = change[1]
        # the problem here is that lines in SE XHTML are different from
        # the lines in PG plain text, so we need to control the amount
        # of context --
        # get the index of the actual change; because the removal of a
        # space will make the lengths of the word lists different, step
        # downward through possible lengths
        extent = max(len(self.before), len(self.after))
        while True:
            try:
                # this should be (and will be) actuals
                self.actual = [
                    self.before[i] != self.after[i] for i in range(extent)
                ].index(True)
                break
            except IndexError:
                extent -= 1
        # get the bounds of the largest match including the
        # actual change
        (self.x, self.y) = sorted([
            (x, y)
            for x in range(self.actual + 1)
            for y in range(self.actual, len(self.before) + 1)
            if ' '.join(self.before[x:y]) in text
            and self.before[self.actual] in ' '.join(self.before[x:y])
        ], key=lambda tup: tup[1] - tup[0])[-1]
        self.match = ' '.join(self.before[self.x:self.y])
        # get the line number of the match
        (self.idx, self.orig) = [
            (i + 1, j) for i, j
            in enumerate(text.split('\r\n'))
            if self.match in j
        ][0]

    def __str__(self):
        correction = f'{self.before[self.actual]} ==> {self.after[self.actual]}'  # noqa
        return f"""

Line {self.idx}:
{self.orig}
{correction}"""
