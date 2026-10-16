from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"

model = MIMOSA(params)
model.solve()

model.save("run_accreu_mit_then_ada")
