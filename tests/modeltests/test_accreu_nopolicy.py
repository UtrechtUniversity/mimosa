import numpy as np
import pytest

from tests.modeltests.utils import (
    read_output,
    assert_saved_regional_output,
    SimulationObjectModel,
)

pytestmark = pytest.mark.simulation


@pytest.fixture(scope="module")
def script_output(accreu_nopolicy_output):
    """Runs the script shown in the documentation."""
    return accreu_nopolicy_output


def test_successful_simulation(script_output):
    assert isinstance(script_output["sim"], SimulationObjectModel)


def test_zero_mitigation_and_adaptation(script_output):
    output = read_output(script_output["model"], simulation=True)
    for variable in ("relative_abatement", "mitigation_costs_abs", "adaptation_costs_abs"):
        assert np.abs(output.loc[variable, "2025":].to_numpy()).max() == pytest.approx(0, abs=1e-9)


def test_emissions_equal_baseline_emissions(script_output):
    output = read_output(script_output["model"], simulation=True)
    np.testing.assert_allclose(
        output.loc["regional_emissions", "2025":],
        output.loc["baseline_emissions", "2025":],
        rtol=1e-9, atol=1e-9,
    )


def test_saved_results_match_simulation(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
        simulation=script_output["sim"],
    )
