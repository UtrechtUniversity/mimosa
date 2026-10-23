from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

model1 = MIMOSA(params)
model1.solve()
model1.save("run_sim_from_opt_optimisation")

# Then run in simulation mode

# Get the values from the control variables:
# `mitigation_level` is the only control variable in default setting. If there are
# other control variables, you can specify them here as well.
mitigation_level = model1.concrete_model.mitigation_level.extract_values()

# If needed, the control variable values can be changed:
mitigation_level = {key: value * 1.05 for key, value in mitigation_level.items()}

simulation = model1.run_simulation(mitigation_level=mitigation_level)
model1.save_simulation(simulation, "run_sim_from_opt_simulation")
