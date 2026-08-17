from mimosa import MIMOSA, load_params

params = load_params()

model1 = MIMOSA(params)
model1.solve()

model1.save("run1_fix")

simulation = model1.run_nopolicy_baseline()

model1.save_simulation(simulation, "baseline1_fix")
