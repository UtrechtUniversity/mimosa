from mimosa import MIMOSA, load_params

params = load_params()

params["emissions"]["carbonbudget"] = "500 GtCO2"  # (1)!

model1 = MIMOSA(params)
model1.solve()

model1.save("run_example1")
