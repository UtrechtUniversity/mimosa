from mimosa import MIMOSA, load_params

regime = "PUT_YOUR_EFFORT_SHARING_REGIME_HERE"  # (1)!

params = load_params()
params["model structure"]["effortsharing module"] = regime

params["model structure"]["damage module"] = "ACCREU"
params["model structure"]["emissiontrade module"] = "emissiontrade"
params["model structure"]["welfare module"] = "cost_minimising"
params["emissions"]["carbonbudget"] = "700 GtCO2"
params["economics"]["MAC"]["rel_mitigation_costs_min_level"] = -0.5

model_effortsharing = MIMOSA(params)
model_effortsharing.solve()
model_effortsharing.save(f"run_{regime}")
