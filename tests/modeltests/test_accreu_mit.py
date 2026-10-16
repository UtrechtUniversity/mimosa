import numpy as np
import pytest

from tests.modeltests.utils import (
    read_output,
    assert_saved_regional_output,
    SolverStatus,
)

pytestmark = pytest.mark.ipopt


@pytest.fixture(scope="module")
def script_output(accreu_mit_output):
    """Runs the script shown in the documentation."""
    return accreu_mit_output


def test_run_successfully(script_output):
    assert script_output["model"].status == SolverStatus.ok


def test_mitigation_without_adaptation(script_output):
    output = read_output(script_output["model"])
    assert output.loc["relative_abatement", "2025":].max().max() > 0
    assert output.loc["mitigation_costs_abs", "2025":].max().max() > 0
    adaptation_costs = output.loc["adaptation_costs_abs", "2025":].to_numpy()
    assert np.abs(adaptation_costs).max() == pytest.approx(0, abs=1e-9)


def test_cumulative_emissions_below_nopolicy(script_output, accreu_nopolicy_output):
    model = script_output["model"]
    output = read_output(model)
    baseline = read_output(accreu_nopolicy_output["model"], simulation=True)
    end_year = str(model.params["time"]["end"])
    emissions = output.loc[("global_cumulative_emissions", "Global"), end_year]
    baseline_emissions = baseline.loc[("global_cumulative_emissions", "Global"), end_year]
    assert emissions < baseline_emissions


def test_saved_results_match_model(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
    )
