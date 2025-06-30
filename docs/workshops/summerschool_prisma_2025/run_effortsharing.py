from mimosa import MIMOSA, load_params

regime = "equal_mitigation_costs"  # (1)!

params = load_params()
params["effort sharing"]["regime"] = regime

params["model"]["emissiontrade module"] = "emissiontrade"
params["model"]["welfare module"] = "cost_minimising"
params["emissions"]["carbonbudget"] = "700 GtCO2"
params["emissions"]["baseline carbon intensity"] = False
params["economics"]["MAC"]["rel_mitigation_costs_min_level"] = -0.5
params["time"]["end"] = 2100

model1 = MIMOSA(params)
model1.solve()
model1.save(f"run_{regime}")
