import pytest

from mimosa.common import quant
from tests.modeltests.utils import exec_run, SolverStatus, read_output


@pytest.fixture(scope="module")
def script_output():
    return exec_run("runs/run_multipleruns.py")


@pytest.mark.slow
def test_run_successfully(script_output):
    # Note: only tests if the last run was successful
    model = script_output["model3"]
    assert model.status == SolverStatus.ok


@pytest.mark.slow
def test_cumulative_emissions_carbon_budgets(script_output):

    for budget in ["500 GtCO2", "700 GtCO2", "1000 GtCO2"]:
        output_df_ind = read_output(filename=f"run_example3_{budget}")

        param_carbonbudget = quant(budget, "emissions_unit")

        cum_emissions = output_df_ind.loc[("cumulative_emissions", "Global")]
        assert cum_emissions["2100"] <= param_carbonbudget
        assert cum_emissions.iloc[-1] <= param_carbonbudget
