from mimosa import MIMOSA, load_params


# Loop over the three available effort sharing regimes
for regime in [
    "equal_mitigation_costs",
    "equal_total_costs",
    "per_cap_convergence",
    "ability_to_pay",
    "equal_cumulative_per_cap",
]:
    params = load_params()
    params["model"]["emissiontrade module"] = "emissiontrade"
    params["model"]["welfare module"] = "cost_minimising"
    params["emissions"]["carbonbudget"] = "700 GtCO2"
    params["emissions"]["baseline carbon intensity"] = False
    params["effort sharing"]["regime"] = regime
    params["economics"]["MAC"]["rel_mitigation_costs_min_level"] = -0.5
    params["time"]["end"] = 2100

    model1 = MIMOSA(params)
    model1.solve()
    model1.save(f"run_{regime}")
