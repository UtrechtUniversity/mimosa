from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"

model = MIMOSA(params)
sim = model.run_simulation()

model.save_simulation(sim, "run_accreu_ada")
