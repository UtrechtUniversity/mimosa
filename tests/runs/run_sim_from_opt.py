from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

model1 = MIMOSA(params)
model1.solve()
model1.save("run_sim_from_opt_optimisation")

# Then run in simulation mode

# Get the values from the control variables:
# `relative_abatement` is the only control variable in default setting. If there are
# other control variables, you can specify them here as well.
relative_abatement = model1.concrete_model.relative_abatement.extract_values()

# If needed, the control variable values can be changed:
relative_abatement = {key: value * 1.05 for key, value in relative_abatement.items()}

simulation = model1.run_simulation(relative_abatement=relative_abatement)
model1.save_simulation(simulation, "run_sim_from_opt_simulation")
