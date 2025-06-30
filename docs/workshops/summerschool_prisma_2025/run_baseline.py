from mimosa import MIMOSA, load_params

params = load_params()

params["economics"]["damages"]["ignore damages"] = False
params["time"]["end"] = 2150

model = MIMOSA(params)

simulation = model.run_nopolicy_baseline()

model.save_simulation(simulation, "run_baseline_nopolicy")
