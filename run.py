from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

model1 = MIMOSA(params)
model1.solve()
model1.save("run1")

# Then do a no-policy run in simulation mode

simulation = model1.run_nopolicy_baseline()
model1.save_simulation(simulation, "run1_baseline_nopolicy")
