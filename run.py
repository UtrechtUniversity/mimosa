from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()
params["time"]["dt"] = 10
params["time"]["end"] = 2300
params["emissions"]["non increasing emissions after 2100"] = False
params["model structure"]["tipping points options"]["include PFAT"] = True


model1 = MIMOSA(params)
model1.solve()
model1.save("model_structure_PFAT_only_test_3")
