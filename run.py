from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

# DEBUG: Print alle regional parameter files

model1 = MIMOSA(params)
model1.solve()
model1.save("run_inequality_6")
