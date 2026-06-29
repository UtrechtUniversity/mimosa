from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

params["model"]["welfare module"] = "cost_minimising"

model1 = MIMOSA(params)
model1.solve()
model1.save("20260629_-_cost_minimising")