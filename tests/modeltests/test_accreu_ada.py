import numpy as np
import pytest

from tests.modeltests.utils import (
    exec_run,
    read_output,
    assert_saved_regional_output,
    SimulationObjectModel,
)

from mimosa.common import value
from mimosa.components.damages.accreu.utils import get_adaptation_calibration

pytestmark = pytest.mark.simulation


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation."""
    return exec_run("runs/run_accreu_ada.py")


def test_successful_simulation(script_output):
    assert isinstance(script_output["sim"], SimulationObjectModel)


def test_zero_mitigation_and_baseline_emissions(script_output):
    output = read_output(script_output["model"], simulation=True)
    assert np.abs(output.loc["mitigation_costs_abs", "2025":].to_numpy()).max() == pytest.approx(0, abs=1e-9)
    np.testing.assert_allclose(
        output.loc["regional_emissions", "2025":],
        output.loc["baseline_emissions", "2025":], rtol=1e-9, atol=1e-9,
    )


def test_positive_adaptation_expenditure(script_output):
    output = read_output(script_output["model"], simulation=True)
    assert output.loc["adaptation_costs_abs", "2025":].max().max() > 0


def test_effectiveness_within_configured_maximum(script_output):
    sim = script_output["sim"]
    model = script_output["model"].concrete_model
    calibration_name = script_output["model"].params["economics"]["damages"]["accreu"]["adaptation_calibration"]
    for sector in ("labourprod", "riverine", "slr"):
        calibration = get_adaptation_calibration(calibration_name, sector)
        for region in sim.regions:
            source_maximum = value(getattr(model, sector + "_adaptation_max_effectiveness")[region])
            maximum = (
                source_maximum * calibration.max_effectiveness_scale
                * value(model.adaptation_effectiveness_scale_factor)
            )
            effectiveness = [getattr(sim, sector + "_avoided_damages_adapt")[t, region] for t in sim.t]
            assert min(effectiveness) >= -1e-9
            assert max(effectiveness) <= maximum + 1e-9


def test_residual_damages_and_total_adaptation_costs(script_output):
    sim = script_output["sim"]
    total_costs = np.zeros_like(sim.adaptation_costs_abs.values)
    for sector in ("labourprod", "riverine", "slr"):
        gross = getattr(sim, sector + "_damage_costs_gross").values
        effectiveness = getattr(sim, sector + "_avoided_damages_adapt").values
        residual = getattr(sim, sector + "_damage_costs").values
        np.testing.assert_allclose(residual, gross * (1 - effectiveness), rtol=1e-9, atol=1e-9)
        total_costs += getattr(sim, sector + "_adaptation_costs_abs").values
    np.testing.assert_allclose(sim.adaptation_costs_abs.values, total_costs, rtol=1e-9, atol=1e-9)


def test_saved_results_match_simulation(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
        simulation=script_output["sim"],
    )
