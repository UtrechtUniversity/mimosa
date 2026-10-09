from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["damage module"] = "ACCREU"

model = MIMOSA(params)
model.solve()

model.save("run_accreu_mit")
