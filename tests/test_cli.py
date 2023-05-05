import pytest
from click.testing import CliRunner
from pgreport.cli import run
import io
import re
import json


@pytest.fixture
def index():
    with open('tests/41981.html') as f:
        return f.read()


@pytest.fixture
def jewels():
    # use io.open so as to leave CRLF endings untouched
    with io.open('tests/pg41981.txt', newline='') as f:
        return f.read()


@pytest.fixture
def mock(requests_mock, index, jewels):
    requests_mock.get(
        'https://www.gutenberg.org/ebooks/41981',
        text=index
    )
    requests_mock.get(
        'https://www.gutenberg.org/ebooks/41981.txt.utf-8',
        text=jewels
    )


def test_single_commit(mock):
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '094f64f'
    ])

    assert result.exit_code == 0
    assert "File: 41981.txt.utf-8" in result.output
    assert "Line 5966:" in result.output
    assert "it's ==> its" in result.output


def test_single_commit_multi_changes_including_on_second_line(mock):
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '20ba626'
    ])

    assert result.exit_code == 0
    assert "19 errors" in result.output
    assert "File: 41981.txt.utf-8" in result.output

    assert 'Line 3507:\nwind-burned."\nwind-burned." ==> windburned."' in result.output  # noqa


def test_single_commit_multi_changes_in_one_line(mock):
    # Test commit #1 for pgreport
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '9170165'
    ])

    assert result.exit_code == 0
    assert "Line 2024:\nJordde suddenly seized up a marlin pin, raised it, and shouted at Urson,\nup a marlin pin, ==> a marlinspike," in result.output  # noqa


def test_multi_commit(mock):
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '20ba626', '7f0e409'
    ])
    assert result.exit_code == 0
    assert "20 errors" in result.output
    assert "File: 41981.txt.utf-8" in result.output
    m = re.findall(r'Line \d+:', result.output)
    assert [int(g[4:-1]) for g in m] == [
        347,
        4993,
        5104,
        5201,
        5399,
        5944,
        6036,
        6283,
        6365,
        1359,
        2100,
        2423,
        2826,
        2967,
        3102,
        3507,
        3509,
        3517,
        4550,
        3138
    ]


def test_single_commit_json(mock):
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '094f64f',
        '--output', 'json'
    ])

    assert result.exit_code == 0
    with open('tests/094f64f.json') as f:
        assert json.load(f) == json.loads(result.output)


def test_change_in_line_with_ellipses(mock):
    # Test commit #2 for pgreport
    # this doesn't really test a change *containing* an ellipse
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', 'bf127d6'
    ])

    assert result.exit_code == 0
    assert 'Line 2369:\n"Where?" asked Geo. "Huh...?" Through the thick growth was a rising\ngrowth ==> undergrowth' in result.output  # noqa


def test_change_including_ellipse(mock):
    # Test commit #3 for pgreport
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '404049e'
    ])

    assert result.exit_code == 0
    assert 'Line 3366' in result.output
    assert 'they...?" ==> you think they...?" he began.' in result.output


def test_expansion_of_context(mock):
    """
    Where the part of the correction before '==>' occurs more than once in the
    PG source line, we need to disambiguate by adding context, so this commit's
    correction should not be 'the ==> his'
    """
    # Test commit #4 for pgreport
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', 'db275a4'
    ])

    assert result.exit_code == 0
    assert 'the ==> his' not in result.output
    assert 'brought the ==> brought his' in result.output
