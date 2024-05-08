import pytest


from tests.modeltests.utils import exec_run, SolverStatus, read_output


@pytest.fixture(scope="module")
def script_output():
    return exec_run("runs/run_base.py")


@pytest.mark.slow
def test_run_successfully(script_output):
    assert script_output["model1"].status == SolverStatus.ok


@pytest.mark.slow
def test_outputfile_exists(script_output):
    model = script_output["model1"]
    read_output(model)


@pytest.mark.slow
def test_cba_temperature(script_output):
    model = script_output["model1"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc[("temperature", "Global"), "2100"] == pytest.approx(
        1.899, abs=0.05
    )
