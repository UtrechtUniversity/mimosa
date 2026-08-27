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
