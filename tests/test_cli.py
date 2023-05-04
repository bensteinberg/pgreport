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


@pytest.mark.xfail(reason='Not yet implemented')
def test_single_commit_multi_changes_in_one_line(mock):
    runner = CliRunner()
    result = runner.invoke(run, [
        'tests/samuel-r-delany_the-jewels-of-aptor', '9170165'
    ])

    assert result.exit_code == 0
    assert result.output.endswith("Line 2024:\nup a marlin pin, ==> a marlinspike,")  # noqa


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
