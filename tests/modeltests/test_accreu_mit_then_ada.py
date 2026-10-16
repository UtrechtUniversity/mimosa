import numpy as np
import pytest

from tests.modeltests.utils import (
    exec_run,
    read_output,
    assert_saved_regional_output,
    SolverStatus,
)

pytestmark = pytest.mark.ipopt


@pytest.fixture(scope="module")
def script_output():
    """Runs the script shown in the documentation."""
    return exec_run("runs/run_accreu_mit_then_ada.py")


def test_run_successfully(script_output):
    model = script_output["model"]
    assert model.status == SolverStatus.ok
    assert model.workflow_control_values is not None


def test_mitigation_matches_mitigation_only_run(script_output, accreu_mit_output):
    output = read_output(script_output["model"])
    mitigation_only = read_output(accreu_mit_output["model"])
    np.testing.assert_allclose(
        output.loc["relative_abatement", "2025":],
        mitigation_only.loc["relative_abatement", "2025":], rtol=1e-7, atol=1e-8,
    )


def test_positive_adaptation_expenditure(script_output):
    output = read_output(script_output["model"])
    assert output.loc["adaptation_costs_abs", "2025":].max().max() > 0


def test_transferred_controls_reproduce_saved_pathway(script_output):
    model = script_output["model"]
    replay = model.run_simulation(**model.workflow_control_values)
    assert_saved_regional_output(
        model,
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "consumption"],
        simulation=replay, saved_simulation=False,
    )


def test_workflow_matches_manual_replay(script_output, accreu_mit_output):
    model = script_output["model"]
    mitigation_model = accreu_mit_output["model"]
    controls = model._extract_compatible_controls(mitigation_model)
    manual_result = model.run_simulation(**controls)

    for variable in (
        "relative_abatement", "temperature", "adaptation_costs_abs",
        "damage_costs_abs", "avoided_damage_costs",
        "global_avoided_damage_costs", "total_direct_costs_abs",
    ):
        actual = list(getattr(model.concrete_model, variable).extract_values().values())
        expected = list(getattr(manual_result, variable).extract_values().values())
        np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=1e-9)
    assert model.status == mitigation_model.status


def test_avoided_damages_use_nopolicy_reference(script_output, accreu_mit_output):
    model = script_output["model"].concrete_model
    reference = accreu_mit_output["model"].concrete_model
    baseline = np.asarray(list(reference.nopolicy_damage_costs.extract_values().values()))
    damages = np.asarray(list(model.damage_costs.extract_values().values()))
    avoided = np.asarray(list(model.avoided_damage_costs.extract_values().values()))

    np.testing.assert_allclose(avoided, baseline - damages, rtol=1e-7, atol=1e-9)
    assert np.isfinite(avoided).all()


def test_saved_results_match_model(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
    )
