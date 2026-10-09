import pytest

from tests.modeltests.utils import exec_run


@pytest.fixture(scope="session")
def accreu_nopolicy_output():
    return exec_run("runs/run_accreu_nopolicy.py")


@pytest.fixture(scope="session")
def accreu_mit_output():
    return exec_run("runs/run_accreu_mit.py")
