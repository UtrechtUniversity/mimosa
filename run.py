from mimosa import MIMOSA, load_params

params = load_params()

params["economics"]["damages"]["ignore damages"] = False
params["time"]["end"] = 2150
params["model"]["damage module"] = "ACCREU"

model = MIMOSA(params)

simulation = model.run_nopolicy_baseline()

model.save_simulation(simulation, "baseline_nopolicy_accreu_newslr")
