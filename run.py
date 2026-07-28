from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()
params["time"]["dt"] = 10
params["time"]["end"] = 2300
params["emissions"]["non increasing emissions after 2100"] = False
params["tippingpoints"]["LABC"]["include"] = True
params["tippingpoints"]["AMOC"]["include"] = True
params["tippingpoints"]["AMAZ"]["include"] = True


model1 = MIMOSA(params)
model1.solve()
model1.save("test_with_tipping_params_false_fix")
