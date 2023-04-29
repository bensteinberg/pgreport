import click
from pathlib import Path
import xml.etree.ElementTree as ET
import pygit2
import re
import requests
from bs4 import BeautifulSoup
import humanize


pg = 'https://www.gutenberg.org'


@click.command()
@click.argument('repo')
@click.argument('commits', nargs=-1)
@click.option('--style',
              type=click.Choice(['PG', 'SE'], case_sensitive=False),
              default='SE')
# add a mechanism for expressing the type of change:
# error in OCR, typo in printed text, other?
def run(repo, commits, style):
    """
    This is an experiment in generating error reports for Project Gutenberg
    from diffs in Standard Ebooks repositories.

    Run with a path to a REPO and the hashes for one or more COMMITS.
    """
    (title, author, source_url) = se_data(repo)

    (release_date, filename, text) = pg_data(source_url)

    corrections = get_corrections(repo, commits, text)

    # prepare output
    s = '' if len(corrections) == 1 else 's'
    count = humanize.apnumber(len(corrections))
    msg = f"""Hi, I’ve been proofing {title} and found {count} error{s}:

Title: {title}, by {author}
Release Date: {release_date} [EBook #{source_url.split("/")[-1]}]

File: {filename}"""

    for c in corrections:
        if style == 'SE':
            msg += c.se()
        elif style == 'PG':
            msg += c.pg()

    click.echo(msg)


def get_corrections(repo, commits, text):
    repository = pygit2.Repository(repo)
    corrections = []

    for commit in commits:
        # get the diff between the specified commit (or HEAD)
        # and the previous one
        base = repository.revparse_single(commit)
        diff = repository.diff(base.parents[0], base)

        if changes := clean_patch(diff.patch):
            for change in changes:
                corrections.append(Correction(change, text))
    return corrections


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

    def se(self):
        m = re.search(r'^(\s+)', self.orig)
        leading = m.group(1) if m else ''
        correction = f"{leading}{' '.join(self.after[self.x:self.y])}"
        return self._output(correction)

    def pg(self):
        correction = f'{self.before[self.actual]} ==> {self.after[self.actual]}'  # noqa
        return self._output(correction)

    def _output(self, correction):
        return f"""

Line {self.idx}:
{self.orig}
{correction}"""


def se_data(repo):
    # read SE epub metadata
    opf = Path(repo) / 'src/epub/content.opf'
    root = ET.parse(opf).getroot()
    # get the PG source URL
    source_url = root.find('.//{http://purl.org/dc/elements/1.1/}source').text
    if not source_url.startswith(pg):
        # but maybe this can be extended to non-PG sources
        raise click.ClickException('The source is not PG')
    # get the title
    title = root.find('.//{http://purl.org/dc/elements/1.1/}title').text
    # get the author
    author = root.find('.//{http://purl.org/dc/elements/1.1/}creator').text
    return (title, author, source_url)


def pg_data(source_url):
    # get the URL of the book's plain text from PG
    r1 = requests.get(source_url)
    soup = BeautifulSoup(r1.text, 'html.parser')
    text_url = soup.find(
        'td',
        property='dcterms:format',
        content='text/plain'
    ).a.attrs['href']
    filename = text_url.split("/")[-1]
    # get the PG release date
    release_date = soup.find(
        'td',
        itemprop='datePublished'
    ).string
    # get the book's plain text
    r2 = requests.get(pg + text_url)
    text = r2.text
    return (release_date, filename, text)


def clean_patch(patch):
    """
    Reduce an SE patch to pairs of cleaned lines suitable
    for reporting to PG
    """
    befores = extract_text(patch, '-')
    afters = extract_text(patch, '+')

    assert len(befores) == len(afters)

    return [
        (befores[i].split(), afters[i].split())
        for i in range(len(befores))
    ]


def extract_text(p, marker):
    # this may need to do additional work, like undoing SE ellipse-handling
    return [
        re.sub(
            '<[^<]+?>', '', line[4:]
        ).replace(
            '“', '"'
        ).replace(
            '”', '"'
        ).replace(
            '’', "'"
        ).replace(
            '‘', "'"
        )
        for line in p.split('\n')
        if line.startswith(f'{marker}\t')
    ]
