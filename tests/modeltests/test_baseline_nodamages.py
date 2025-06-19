import pytest
from tests.modeltests.utils import exec_run, SimulationObjectModel, read_output

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_baseline_nodamages.py")


def test_successful_simulation(script_output):
    """Simulation object should be created"""
    assert isinstance(script_output["simulation"], SimulationObjectModel)


def test_zero_mitigation_costs(script_output):
    """Mitigation costs should be zero"""
    model = script_output["model"]
    output_df_ind = read_output(model, simulation=True)

    assert output_df_ind.loc[
        "mitigation_costs", "2020":"2100"
    ].max().max() == pytest.approx(0.0, abs=0.001)


def test_carbonprice_zero(script_output):
    """Carbon price should be zero"""
    model = script_output["model"]
    output_df_ind = read_output(model, simulation=True)

    assert output_df_ind.loc["carbonprice", "2020":"2100"].max().max() == pytest.approx(
        0.0, abs=0.001
    )


def test_emissions_equal_to_baseline_emissions(script_output):
    """Regional eissions should be equal to baseline emissions"""
    model = script_output["model"]
    output_df_ind = read_output(model, simulation=True)

    baseline = output_df_ind.loc["baseline", "2020":]
    emissions = output_df_ind.loc["regional_emissions", "2020":]

    diff = (baseline - emissions) / baseline
    assert diff.abs().max().max() < 0.01  # Maximum difference should be less than 1%


def test_gdp_equal_to_baseline_gdp(script_output):
    """GDP should be equal to baseline GDP"""
    model = script_output["model"]
    output_df_ind = read_output(model, simulation=True)

    baseline = output_df_ind.loc["baseline_GDP", "2020":]
    gdp = output_df_ind.loc["GDP_net", "2020":]

    diff = (baseline - gdp) / baseline
    assert diff.abs().stack().max() < 0.01
    assert diff.abs().stack().mean() < 0.01
