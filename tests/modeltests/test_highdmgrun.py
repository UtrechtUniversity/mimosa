import pytest


from tests.modeltests.utils import exec_run, SolverStatus, read_output


@pytest.fixture(scope="module")
def script_output():
    return exec_run("runs/run_high_dmg_tcre_low_prtp.py")


@pytest.mark.slow
def test_run_successfully(script_output):
    assert script_output["model2"].status == SolverStatus.ok


@pytest.mark.slow
def test_cba_temperature(script_output):
    model = script_output["model2"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc[("temperature", "Global"), "2100"] < 1.6
