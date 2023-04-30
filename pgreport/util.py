from pathlib import Path
import xml.etree.ElementTree as ET
import pygit2
import re
import requests
from bs4 import BeautifulSoup

from pgreport.cls import Correction


pg = 'https://www.gutenberg.org'


def get_corrections(repo, commits, text, style):
    repository = pygit2.Repository(repo)
    corrections = []

    for commit in commits:
        # get the diff between the specified commit (or HEAD)
        # and the previous one
        base = repository.revparse_single(commit)
        diff = repository.diff(base.parents[0], base)

        if changes := clean_patch(diff.patch):
            for change in changes:
                corrections.append(Correction(change, text, style))
    return corrections


def se_data(repo):
    # read SE epub metadata
    opf = Path(repo) / 'src/epub/content.opf'
    root = ET.parse(opf).getroot()
    # get the PG source URL
    source_url = root.find('.//{http://purl.org/dc/elements/1.1/}source').text
    assert source_url.startswith(pg)
    # but maybe this can be extended to non-PG sources
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
