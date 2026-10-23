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
    return exec_run("runs/run_accreu_mit_ada_joint.py")


def test_run_successfully(script_output):
    assert script_output["model"].status == SolverStatus.ok


def test_positive_mitigation_and_adaptation(script_output):
    output = read_output(script_output["model"])
    assert output.loc["mitigation_costs_abs", "2025":].max().max() > 0
    assert output.loc["adaptation_costs_abs", "2025":].max().max() > 0


def test_analytical_adaptation_is_not_a_simulation_control(script_output):
    model = script_output["model"]
    assert model.params["economics"]["damages"]["accreu"][
        "adaptation_determination"
    ] == "analytical_optimum"
    assert model._uses_sequential_accreu_cba() is False
    assert not any("adaptation" in name for name in model.simulator.control_variables)


def test_final_temperature_above_mitigation_only_run(script_output, accreu_mit_output):
    model = script_output["model"]
    output = read_output(model)
    mitigation_only = read_output(accreu_mit_output["model"])
    end_year = str(model.params["time"]["end"])

    assert output.loc[("temperature", "Global"), end_year] > mitigation_only.loc[
        ("temperature", "Global"), end_year
    ]


def test_control_replay_matches_solved_results(script_output):
    model = script_output["model"]
    controls = {
        name: getattr(model.concrete_model, name).extract_values()
        for name in model.simulator.control_variables
    }
    replay = model.run_simulation(**controls)
    assert_saved_regional_output(
        model,
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "consumption"],
        simulation=replay, saved_simulation=False,
    )


def test_saved_results_match_model(script_output):
    assert_saved_regional_output(
        script_output["model"],
        ["regional_emissions", "damage_costs_abs", "adaptation_costs_abs", "mortality_net"],
    )
