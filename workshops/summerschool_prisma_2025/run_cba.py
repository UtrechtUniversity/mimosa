from mimosa import MIMOSA, load_params

params = load_params()

# Set the carbon budget to False to run without carbon budget constraint
params["emissions"]["carbonbudget"] = False

model2 = MIMOSA(params)

model2.solve()

model2.save("run_cba")
