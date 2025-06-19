from mimosa import MIMOSA, load_params

params = load_params()
params["economics"]["damages"]["ignore damages"] = False
params["time"]["end"] = 2150

model1 = MIMOSA(params)
simulation_nopolicy = model1.run_nopolicy_baseline()
model1.save_simulation(simulation_nopolicy, "baseline_nopolicy")

params = load_params()
params["economics"]["damages"]["ignore damages"] = True
params["economics"]["damages"]["scale factor"] = 0
params["time"]["end"] = 2150

model2 = MIMOSA(params)
simulation_nodamages = model2.run_nopolicy_baseline()
model2.save_simulation(simulation_nodamages, "baseline_nodamages")
