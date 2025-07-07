from mimosa import MIMOSA, load_params

regime = "PUT_YOUR_EFFORT_SHARING_REGIME_HERE"  # (1)!

params = load_params()
params["effort sharing"]["regime"] = regime

params["model"]["emissiontrade module"] = "emissiontrade"
params["model"]["welfare module"] = "cost_minimising"
params["emissions"]["carbonbudget"] = "700 GtCO2"
params["emissions"]["baseline carbon intensity"] = False
params["economics"]["MAC"]["rel_mitigation_costs_min_level"] = -0.5
params["time"]["end"] = 2100

model3 = MIMOSA(params)
model3.solve()
model3.save(f"run_{regime}")
