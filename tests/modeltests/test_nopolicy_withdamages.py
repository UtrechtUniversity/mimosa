import pytest
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_nopolicy_withdamages.py")


def test_run_successfully(script_output):
    """Run should be successful"""
    assert script_output["model"].status == SolverStatus.ok


def test_zero_mitigation_costs(script_output):
    """Mitigation costs should be zero"""
    model = script_output["model"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc[
        "mitigation_costs", "2020":"2100"
    ].max().max() == pytest.approx(0.0, abs=0.001)


def test_carbonprice_zero(script_output):
    """Carbon price should be zero"""
    model = script_output["model"]
    output_df_ind = read_output(model)

    assert output_df_ind.loc["carbonprice", "2020":"2100"].max().max() == pytest.approx(
        0.0, abs=0.001
    )


def test_emissions_equal_to_baseline_emissions(script_output):
    """Regional eissions should be equal to baseline emissions"""
    model = script_output["model"]
    output_df_ind = read_output(model)

    baseline = output_df_ind.loc["baseline", "2020":]
    emissions = output_df_ind.loc["regional_emissions", "2020":]

    diff = (baseline - emissions) / baseline
    assert diff.abs().max().max() < 0.05  # Maximum difference should be less than 5%


def test_damages_not_ignored(script_output):
    """Damages should not be ignored"""
    model = script_output["model"]
    output_df_ind = read_output(model)

    damages = output_df_ind.loc["damage_costs", "2020":]

    assert (
        damages.max().max() > 0.1
    )  # Damages should at least reach 10% of GDP at some point


def test_gdp_below_to_baseline_gdp(script_output):
    """Net GDP should be significantly lower than baseline GDP"""
    model = script_output["model"]
    output_df_ind = read_output(model)

    baseline = output_df_ind.loc["baseline_GDP", "2020":]
    gdp = output_df_ind.loc["GDP_net", "2020":]

    diff = (baseline - gdp) / baseline
    assert diff.abs().stack().max() > 0.15  # Maximum difference should be more than 15%

    # Mean difference between baseline and actual GDP in 2100 should be more than 10%:
    assert diff["2100"].mean() > 0.1
