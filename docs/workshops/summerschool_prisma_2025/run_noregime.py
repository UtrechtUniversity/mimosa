from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["welfare module"] = "cost_minimising"
params["emissions"]["carbonbudget"] = "700 GtCO2"
params["time"]["periods"] = {2100: 5}

model4 = MIMOSA(params)
model4.solve()
model4.save("run_cost_minimising")
