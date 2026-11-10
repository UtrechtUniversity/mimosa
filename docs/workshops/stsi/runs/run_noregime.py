from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["welfare module"] = "cost_minimising"

params["model structure"]["damage module"] = "ACCREU"
params["emissions"]["carbonbudget"] = "700 GtCO2"
params["time"]["end"] = 2100

model_noregime = MIMOSA(params)
model_noregime.solve()
model_noregime.save("run_cost_minimising")
