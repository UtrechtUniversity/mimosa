import pytest


from tests.modeltests.utils import exec_run, SolverStatus, read_output


@pytest.fixture(scope="module")
def script_output():
    return exec_run("runs/run_baseline_nodamages.py")


@pytest.mark.slow
def test_run_successfully(script_output):
    assert script_output["model"].status == SolverStatus.ok


@pytest.mark.slow
def test_zero_mitigation_costs(script_output):
    model = script_output["model"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc[
        "mitigation_costs", "2020":"2100"
    ].max().max() == pytest.approx(0.0, abs=0.001)


@pytest.mark.slow
def test_carbonprice_zero(script_output):
    model = script_output["model"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc["carbonprice", "2020":"2100"].max().max() == pytest.approx(
        0.0, abs=0.001
    )


@pytest.mark.slow
def test_emissions_equal_to_baseline(script_output):
    model = script_output["model"]
    output_df_ind = read_output(model)

    baseline = output_df_ind.loc["baseline", "2020":]
    emissions = output_df_ind.loc["regional_emissions", "2020":]

    diff = (baseline - emissions) / baseline
    assert diff.abs().max().max() < 0.05  # Maximum difference should be less than 5%
