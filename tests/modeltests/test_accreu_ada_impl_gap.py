import numpy as np
import pytest

from tests.modeltests.utils import (
    exec_run,
    assert_saved_regional_output,
    SimulationObjectModel,
)

from mimosa.common import value
from mimosa.components.damages.accreu.utils import (
    adaptation_effectiveness_fct,
    effective_adaptation_curve,
    get_adaptation_calibration,
)

pytestmark = pytest.mark.simulation


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation."""
    return exec_run("runs/run_accreu_ada_impl_gap.py")


def test_successful_simulation(script_output):
    assert isinstance(script_output["sim"], SimulationObjectModel)


def test_mitigation_is_unchanged(script_output):
    np.testing.assert_allclose(
        script_output["sim"].relative_abatement.values,
        script_output["sim_ada"].relative_abatement.values,
        rtol=1e-9, atol=1e-9,
    )


def test_expenditure_is_scaled_by_readiness(script_output):
    sim = script_output["sim"]
    reference = script_output["sim_ada"]
    readiness = script_output["adaptation_readiness"]
    ssp = script_output["params"]["SSP"]
    for sector in ("labourprod", "riverine", "slr"):
        costs = getattr(sim, sector + "_adaptation_costs_abs")
        reference_costs = getattr(reference, sector + "_adaptation_costs_abs")
        for t in sim.t:
            year = str(int(sim.year(t)))
            for region in sim.regions:
                expected = readiness.loc[(ssp, region), year] * reference_costs[t, region]
                assert costs[t, region] == pytest.approx(expected, rel=1e-9, abs=1e-9)
                assert costs[t, region] <= reference_costs[t, region] + 1e-9


def test_effectiveness_uses_reduced_expenditure(script_output):
    sim = script_output["sim"]
    model = script_output["model"].concrete_model
    calibration_name = script_output["params"]["economics"]["damages"]["accreu"]["adaptation_calibration"]
    for sector in ("labourprod", "riverine", "slr"):
        calibration = get_adaptation_calibration(calibration_name, sector)
        for region in sim.regions:
            maximum, cost_parameter = effective_adaptation_curve(
                model, region,
                getattr(model, sector + "_adaptation_max_effectiveness")[region],
                getattr(model, sector + "_adaptation_cost_param")[region], calibration,
            )
            for t in sim.t:
                costs = getattr(sim, sector + "_adaptation_costs_abs")[t, region]
                expected = value(adaptation_effectiveness_fct(costs, maximum, cost_parameter))
                effectiveness = getattr(sim, sector + "_avoided_damages_adapt")[t, region]
                assert effectiveness == pytest.approx(expected, rel=1e-9, abs=1e-9)


def test_saved_results_match_simulation(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
        simulation=script_output["sim"],
    )
