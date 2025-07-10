import pytest
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.ipopt


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_base.py")


def test_run_successfully(script_output):
    """Run should be successful"""
    assert script_output["model1"].status == SolverStatus.ok


def test_outputfile_exists(script_output):
    """Output file should exist"""
    model = script_output["model1"]
    read_output(model)


def test_cba_temperature(script_output):
    """Global temperature should be around 1.899°C with default settings."""
    model = script_output["model1"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc[("temperature", "Global"), "2100"] == pytest.approx(
        1.899, abs=0.05
    )
