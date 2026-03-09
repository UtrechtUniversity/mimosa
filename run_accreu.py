from mimosa import MIMOSA, load_params

#### Run 1: CBA with adaptation optimised by MIMOSA

params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
# params["custom_constraints"]["constraint_variables"] = {"slr_avoided_damages": 0}
model1 = MIMOSA(params)
model1.solve()
model1.save("run_accreu_new1")


#### Run 2: no-policy baseline with no adaptation
sim_run2 = model1.run_simulation(slr_adaptation_costs_rel=0.0)
model1.save_simulation(sim_run2, "run_accreu_new2")


# #### Run 3: no-policy baseline with optimal adaptation
# sim_run3 = model1.run_simulation(slr_adaptation_level=1.0)
# model1.save_simulation(sim_run3, "run_accreu_new3")


#### Run 4: Take a MIMOSA optimisation run and just change the adaptation level:

# Relative abatement is the only free variable in the model besides the adaptation level.
# By fixing this to the same values as in run 1, you obtain the same results in simulation
# mode, but now you can easily change the adaptation level
relative_abatement = model1.concrete_model.relative_abatement.extract_values()
sim_run4 = model1.run_simulation(
    relative_abatement=relative_abatement,
    slr_adaptation_costs_rel=0.00002,  # Example value
)
model1.save_simulation(sim_run4, "run_accreu_new4")


# Plot the dependency graph for the equations and variables in the model:
model1.simulator.plot_dependency_graph()
