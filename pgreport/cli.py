import click
import json

from pgreport.cls import Report
from pgreport.util import se_data, pg_data, get_corrections


@click.command()
@click.argument('repo')
@click.argument('commits', nargs=-1)
@click.option('--output',
              type=click.Choice(['text', 'json'], case_sensitive=False),
              default='text', show_default=True)
@click.option('--style',
              type=click.Choice(['PG', 'SE'], case_sensitive=False),
              default='SE', show_default=True)
def run(repo, commits, output, style):
    """
    This is an experiment in generating error reports for Project Gutenberg
    from diffs in Standard Ebooks repositories.

    Run with a path to a REPO and the hashes for one or more COMMITS.
    """
    (title, author, source_url) = se_data(repo)
    number = source_url.split("/")[-1]

    (release_date, filename, text) = pg_data(source_url)

    corrections = get_corrections(repo, commits, text, style)

    r = Report(title, author, release_date, filename, number, corrections)
    if output == 'json':
        click.echo(json.dumps(r, default=vars))
    elif output == 'text':
        click.echo(r)
