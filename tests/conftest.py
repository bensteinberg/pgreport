import pygit2


def pytest_configure(config):
    """
    Ensure submodule is up-to-date.
    """
    repo = pygit2.Repository('.')
    repo.submodules.init()
    repo.submodules.update()
