from mimosa import MIMOSA, load_params

params = load_params()

# Set the carbon budget to False to run without carbon budget constraint
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve()
model1.save("run_cba")
