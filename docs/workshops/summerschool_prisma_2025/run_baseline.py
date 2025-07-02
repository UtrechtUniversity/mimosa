from mimosa import MIMOSA, load_params

params = load_params()

# Make sure that the damages are not ignored. Set this to True if you want a true baseline run without impacts.
params["economics"]["damages"]["ignore damages"] = False

model1 = MIMOSA(params)

simulation1 = model1.run_nopolicy_baseline()

model1.save_simulation(simulation1, "run_baseline_nopolicy")
