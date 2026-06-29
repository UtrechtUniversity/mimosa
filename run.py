from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

params["model"]["welfare module"] = "welfare_loss_minimising"
params["model"]["damage module"] = "COACCH"

model1 = MIMOSA(params)
model1.solve()
model1.save("20260629_-_welfare_loss_minimising")