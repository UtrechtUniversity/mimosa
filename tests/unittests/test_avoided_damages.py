import numpy as np
import pandas as pd
import pytest

from mimosa import MIMOSA, load_params


@pytest.mark.parametrize(
    "damage_module, monetise_mortality",
    [("COACCH", False), ("ACCREU", False), ("ACCREU", True)],
)
def test_policy_simulation_calculates_avoided_damages_after_baseline(
    damage_module, monetise_mortality, tmp_path
):
    params = load_params()
    params["time"]["end"] = 2050
    params["time"]["periods"] = {}
    params["model structure"]["damage module"] = damage_module
    params["economics"]["damages"]["accreu"]["monetise_mortality"] = monetise_mortality

    model = MIMOSA(params, prerun=False)
    baseline = model.run_nopolicy_baseline()
    policy = model.run_simulation(mitigation_level=0.5)

    expected_regional = baseline.damage_costs.values - policy.damage_costs.values
    np.testing.assert_allclose(policy.avoided_damage_costs.values, expected_regional)
    assert np.isfinite(policy.avoided_damage_costs.values).all()

    expected_global = (
        np.sum(expected_regional * policy.GDP_gross.values, axis=1)
        / policy.global_GDP_gross.values
    )
    np.testing.assert_allclose(
        policy.global_avoided_damage_costs.values, expected_global
    )
    assert np.isfinite(policy.global_avoided_damage_costs.values).all()

    baseline_total = (
        baseline.damage_costs.values
        + baseline.non_market_damage_costs_abs.values / baseline.GDP_gross.values
    )
    policy_total = (
        policy.damage_costs.values
        + policy.non_market_damage_costs_abs.values / policy.GDP_gross.values
    )
    expected_total = baseline_total - policy_total
    np.testing.assert_allclose(
        policy.nopolicy_market_and_non_market_damage_costs.values, baseline_total
    )
    np.testing.assert_allclose(
        policy.avoided_market_and_non_market_damage_costs.values, expected_total
    )
    expected_global_total = (
        np.sum(expected_total * policy.GDP_gross.values, axis=1)
        / policy.global_GDP_gross.values
    )
    np.testing.assert_allclose(
        policy.global_avoided_market_and_non_market_damage_costs.values,
        expected_global_total,
    )
    assert np.isfinite(expected_total).all()
    assert np.isfinite(expected_global_total).all()
    if monetise_mortality:
        assert np.any(np.abs(expected_total - expected_regional) > 1e-9)
    else:
        np.testing.assert_allclose(expected_total, expected_regional)
        np.testing.assert_allclose(expected_global_total, expected_global)

    # Global series are already model variables: export must not duplicate them.
    model.save_simulation(policy, "policy", folder=str(tmp_path))
    output = pd.read_csv(tmp_path / "policy.csv")
    global_rows = output[
        output["Variable"] == "global_avoided_market_and_non_market_damage_costs"
    ]
    assert len(global_rows) == 1
    years = [str(int(policy.year(t))) for t in policy.t]
    np.testing.assert_allclose(
        global_rows[years].to_numpy()[0],
        expected_global_total,
        rtol=1e-5,
        atol=1e-12,
    )

    # Repeated baseline calls refresh references without adding duplicate equations.
    model.run_nopolicy_baseline()
    no_policy = model.run_simulation()
    np.testing.assert_allclose(
        no_policy.avoided_market_and_non_market_damage_costs.values, 0, atol=1e-12
    )
    np.testing.assert_allclose(
        no_policy.global_avoided_market_and_non_market_damage_costs.values,
        0,
        atol=1e-12,
    )


def test_analytical_accreu_uses_a_noadaptation_nopolicy_baseline():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}
    params["model structure"]["damage module"] = "ACCREU"
    options = params["economics"]["damages"]["accreu"]
    options["adaptation"] = "sectoral"
    options["adaptation_determination"] = "analytical_optimum"

    model = MIMOSA(params, prerun=False)
    baseline = model.run_nopolicy_baseline()
    adaptation_only = model.run_simulation()

    baseline_options = baseline.params["economics"]["damages"]["accreu"]
    assert baseline_options["adaptation"] == "noadaptation"
    assert np.all(baseline.adaptation_costs.values == 0)
    assert model.params["economics"]["damages"]["accreu"]["adaptation"] == "sectoral"

    expected_avoided = (
        baseline.damage_costs.values - adaptation_only.damage_costs.values
    )
    np.testing.assert_allclose(
        adaptation_only.avoided_damage_costs.values, expected_avoided
    )
    assert np.any(adaptation_only.avoided_damage_costs.values[1:] > 0)

    expected_total = (
        baseline.market_and_non_market_damage_costs.values
        - adaptation_only.market_and_non_market_damage_costs.values
    )
    np.testing.assert_allclose(
        adaptation_only.avoided_market_and_non_market_damage_costs.values,
        expected_total,
        atol=1e-12,
    )
