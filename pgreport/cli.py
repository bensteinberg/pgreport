import click
from pathlib import Path
import xml.etree.ElementTree as ET
import pygit2
import re
import requests
from bs4 import BeautifulSoup
import humanize


@click.command()
@click.option('--repo')
@click.option('--commit', default='HEAD')
@click.option('--style',
              type=click.Choice(['PG', 'SE'], case_sensitive=False),
              default='SE')
# add a mechanism for expressing the type of change:
# error in OCR, typo in printed text, other?
def run(repo, commit, style):
    """
    This is an experiment in generating error reports for Project Gutenberg
    from diffs in Standard Ebooks repositories.
    """
    pg = 'https://www.gutenberg.org'
    opf = Path(repo) / 'src/epub/content.opf'
    root = ET.parse(opf).getroot()
    # get the PG source URL from SE epub metadata
    source_url = root.find('.//{http://purl.org/dc/elements/1.1/}source').text
    if not source_url.startswith(pg):
        # but maybe this can be extended to non-PG sources
        raise click.ClickException('The source is not PG')
    # get the title from SE epub metadata
    title = root.find('.//{http://purl.org/dc/elements/1.1/}title').text
    # get the author from SE epub metadata
    author = root.find('.//{http://purl.org/dc/elements/1.1/}creator').text

    # get the diff between the specified commit (or HEAD)
    # and the previous one
    repository = pygit2.Repository(repo)
    base = repository.revparse_single(commit)
    diff = repository.diff(base.parents[0], base)

    if changes := clean_patch(diff.patch):
        # get the URL of the book's plain text
        r1 = requests.get(source_url)
        soup = BeautifulSoup(r1.text, 'html.parser')
        text_url = soup.find(
            'td',
            property='dcterms:format',
            content='text/plain'
        ).a.attrs['href']
        # get the PG release date
        release_date = soup.find(
            'td',
            itemprop='datePublished'
        ).string
        # get the book's plain text
        r2 = requests.get(pg + text_url)

        # prepare the first part of the message
        c = len(changes)
        s = '' if c == 1 else 's'
        count = humanize.apnumber(c)
        msg = f"""Hi, I’ve been proofing {title} and found {count} error{s}:

Title: {title}, by {author}
Release Date: {release_date} [EBook #{source_url.split("/")[-1]}]

File: {text_url.split("/")[-1]}"""

        for change in changes:
            before = change[0]
            after = change[1]
            # the problem here is that lines in SE XHTML are different from
            # the lines in PG plain text, so we need to control the amount
            # of context --
            # get the index of the actual change; because the removal of a
            # space will make the lengths of the word lists different, step
            # downward through possible lengths
            extent = max(len(before), len(after))
            while True:
                try:
                    actual = [
                        before[i] != after[i] for i in range(extent)
                    ].index(True)
                    break
                except IndexError:
                    extent -= 1
            # get the bounds of the largest match including the actual change;
            (x, y) = sorted([
                (x, y)
                for x in range(actual + 1)
                for y in range(actual, len(before) + 1)
                if ' '.join(before[x:y]) in r2.text
                and before[actual] in ' '.join(before[x:y])
            ], key=lambda tup: tup[1] - tup[0])[-1]
            match = ' '.join(before[x:y])
            # get the line number of the match
            (idx, orig) = [
                (i + 1, j) for i, j
                in enumerate(r2.text.split('\r\n'))
                if match in j
            ][0]
            # prepare correction string
            if style == 'SE':
                # get leading whitespace if any
                m = re.search(r'^(\s+)', orig)
                leading = m.group(1) if m else ''
                correction = f"{leading}{' '.join(after[x:y])}"
            else:
                correction = f'{before[actual]} ==> {after[actual]}'
            msg += f"""

Line {idx}:
{orig}
{correction}"""

        click.echo(msg)


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
