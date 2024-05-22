import pytest
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_high_dmg_tcre_low_prtp.py")


def test_run_successfully(script_output):
    """Run should be successful"""
    assert script_output["model2"].status == SolverStatus.ok


def test_cba_temperature(script_output):
    """
    Global temperature should be below 1.6°C since this is a
    run with high damages, high TCRE and low PRTP.
    """
    model = script_output["model2"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc[("temperature", "Global"), "2100"] < 1.6
