from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

params["model"]["welfare module"] = "welfare_loss_minimising_quintiles"

model1 = MIMOSA(params)
model1.solve()
model1.save("run_inequality_1")
