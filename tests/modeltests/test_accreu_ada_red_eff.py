import numpy as np
import pytest

from tests.modeltests.utils import (
    exec_run,
    assert_saved_regional_output,
    SimulationObjectModel,
)

pytestmark = pytest.mark.simulation


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation."""
    return exec_run("runs/run_accreu_ada_red_eff.py")


def test_successful_simulation(script_output):
    assert isinstance(script_output["sim"], SimulationObjectModel)


def test_mitigation_and_adaptation_expenditure_are_unchanged(script_output):
    sim = script_output["sim"]
    reference = script_output["sim_ada"]
    for variable in (
        "relative_abatement", "labourprod_adaptation_costs_abs",
        "riverine_adaptation_costs_abs", "slr_adaptation_costs_abs",
    ):
        np.testing.assert_allclose(
            getattr(sim, variable).values, getattr(reference, variable).values,
            rtol=1e-9, atol=1e-9,
        )


def test_effectiveness_is_halved(script_output):
    sim = script_output["sim"]
    reference = script_output["sim_ada"]
    for sector in ("labourprod", "riverine", "slr"):
        variable = sector + "_avoided_damages_adapt"
        expected = 0.5 * getattr(reference, variable).values
        np.testing.assert_allclose(getattr(sim, variable).values, expected, rtol=1e-9, atol=1e-9)


def test_larger_unavoided_share_of_gross_damages(script_output):
    sim = script_output["sim"]
    reference = script_output["sim_ada"]
    increases = []
    for sector in ("labourprod", "riverine", "slr"):
        gross = getattr(sim, sector + "_damage_costs_gross").values
        reference_gross = getattr(reference, sector + "_damage_costs_gross").values
        positive_gross = (gross > 1e-9) & (reference_gross > 1e-9)
        residual = getattr(sim, sector + "_damage_costs").values
        reference_residual = getattr(reference, sector + "_damage_costs").values
        # GDP feedback changes emissions and gross damages between runs.
        difference = (
            residual[positive_gross] / gross[positive_gross]
            - reference_residual[positive_gross] / reference_gross[positive_gross]
        )
        assert np.all(difference >= -1e-9)
        increases.extend(difference)
    assert np.max(increases) > 1e-9


def test_saved_results_match_simulation(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
        simulation=script_output["sim"],
    )
