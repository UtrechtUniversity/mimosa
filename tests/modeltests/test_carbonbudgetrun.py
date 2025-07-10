import pytest
from mimosa.common import quant
from tests.modeltests.utils import exec_run, SolverStatus, read_output

pytestmark = pytest.mark.ipopt


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation"""
    return exec_run("runs/run_carbonbudget.py")


def test_run_successfully(script_output):
    """Run should be successful"""
    model = script_output["model1"]
    assert model.status == SolverStatus.ok


def test_cumulative_emissions_carbon_budget(script_output):
    """Cumulative emissions should be below or equal to the carbon budget."""
    model = script_output["model1"]
    output_df_ind = read_output(model)

    param_carbonbudget = quant(
        model.params["emissions"]["carbonbudget"],
        model.preprocessor.parser_tree["emissions"]["carbonbudget"].unit,
    )

    cum_emissions = output_df_ind.loc[("cumulative_emissions", "Global")]
    assert cum_emissions["2100"] <= param_carbonbudget
    assert cum_emissions.iloc[-1] <= param_carbonbudget
