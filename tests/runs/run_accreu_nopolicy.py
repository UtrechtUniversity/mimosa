from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["damage module"] = "ACCREU"

model = MIMOSA(params)
sim = model.run_nopolicy_baseline()

model.save_simulation(sim, "run_accreu_nopolicy")
