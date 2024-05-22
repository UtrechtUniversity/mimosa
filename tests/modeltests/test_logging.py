import pytest
import re
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.slow


def read_log():
    try:
        with open("mainlog.log", "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def _remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix) :]
    return text


@pytest.fixture(scope="module")
def previous_log_output():
    """Reads the content of the log file before running the script"""
    return read_log()


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_logging.py")


def test_run_successfully(previous_log_output, script_output):
    """Run should be successful"""
    assert script_output["model1"].status == SolverStatus.ok


def test_log_output(previous_log_output, script_output):
    """Log file should have at least three new lines with the MIMOSA status, final NPV and solve time"""
    log = read_log()
    new_log = _remove_prefix(log, previous_log_output)

    regex_status = re.compile(r"\[INFO, [0-9-:, ]+\] MIMOSA - Status: ok")
    regex_npv = re.compile(r"\[INFO, [0-9-:, ]+\] MIMOSA - Final NPV: -?[0-9,.]+")
    regex_time = re.compile(
        r"\[INFO, [0-9-:, ]+\] MIMOSA - Model solve took [0-9,.]+ seconds"
    )

    assert len(regex_status.findall(new_log)) >= 1
    assert len(regex_npv.findall(new_log)) >= 1
    assert len(regex_time.findall(new_log)) >= 1
