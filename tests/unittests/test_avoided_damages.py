import numpy as np

from mimosa import MIMOSA, load_params


def test_policy_simulation_calculates_avoided_damages_after_baseline():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}

    model = MIMOSA(params, prerun=False)
    baseline = model.run_nopolicy_baseline()
    policy = model.run_simulation(relative_abatement=0.5)

    expected_regional = baseline.damage_costs.values - policy.damage_costs.values
    np.testing.assert_allclose(policy.avoided_damage_costs.values, expected_regional)
    assert np.isfinite(policy.avoided_damage_costs.values).all()

    expected_global = np.sum(
        expected_regional * policy.GDP_gross.values, axis=1
    ) / policy.global_GDP_gross.values
    np.testing.assert_allclose(
        policy.global_avoided_damage_costs.values, expected_global
    )
    assert np.isfinite(policy.global_avoided_damage_costs.values).all()


def test_analytical_accreu_uses_a_noadaptation_nopolicy_baseline():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation_determination"] = "analytical_optimum"

    model = MIMOSA(params, prerun=False)
    baseline = model.run_nopolicy_baseline()
    adaptation_only = model.run_simulation()

    baseline_options = baseline.params["model structure"]["damage module options"]
    assert baseline_options["ACCREU_adaptation"] == "noadaptation"
    assert np.all(baseline.adaptation_costs.values == 0)
    assert model.params["model structure"]["damage module options"][
        "ACCREU_adaptation"
    ] == "separate"

    expected_avoided = (
        baseline.damage_costs.values - adaptation_only.damage_costs.values
    )
    np.testing.assert_allclose(
        adaptation_only.avoided_damage_costs.values, expected_avoided
    )
    assert np.any(adaptation_only.avoided_damage_costs.values[1:] > 0)
