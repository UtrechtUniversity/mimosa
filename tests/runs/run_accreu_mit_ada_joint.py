from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"
params["economics"]["damages"]["accreu"]["cba_strategy"] = "joint"

model = MIMOSA(params)
model.solve()

model.save("run_accreu_mit_ada_joint")
