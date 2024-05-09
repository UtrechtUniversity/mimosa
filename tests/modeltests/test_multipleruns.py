import pytest

from mimosa.common import quant
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_multipleruns.py")


def test_run_successfully(script_output):
    """
    Last run should be successful. Others also, but those are not
    directly accessible from the script_output. Their success is tested
    since MIMOSA raises an exception if a run fails.
    """
    # Note: only tests if the last run was successful
    model = script_output["model3"]
    assert model.status == SolverStatus.ok


def test_cumulative_emissions_carbon_budgets(script_output):
    """Cumulative emissions should be below or equal to the respective carbon budgets."""

    for budget in ["500 GtCO2", "700 GtCO2", "1000 GtCO2"]:
        output_df_ind = read_output(filename=f"run_example3_{budget}")

        param_carbonbudget = quant(budget, "emissions_unit")

        cum_emissions = output_df_ind.loc[("cumulative_emissions", "Global")]
        assert cum_emissions["2100"] <= param_carbonbudget
        assert cum_emissions.iloc[-1] <= param_carbonbudget
