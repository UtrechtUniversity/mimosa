from mimosa import MIMOSA, load_params

#### Run 1: CBA with adaptation optimised by MIMOSA

params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
model1 = MIMOSA(params)
model1.solve()
model1.save("run_accreu_1_cba_opt_adapt")

#### Run 2a: CBA with no adaptation

params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
params["custom_constraints"]["constraint_variables"] = {"slr_avoided_damages": 0}
model2a = MIMOSA(params)
model2a.solve()
model2a.save("run_accreu_2a_cba_no_adapt")

#### Run 2b: Given mitigation from run 2a, optimise adaptation

params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
params["custom_constraints"]["constraint_variables"] = {
    "relative_abatement": "output/run_accreu_2a_cba_no_adapt.csv"
}
model2b = MIMOSA(params)
model2b.solve()
model2b.save("run_accreu_2b_cba_opt_adapt")


#### Run 3: no-policy baseline with no adaptation
sim_run1 = model1.run_simulation(slr_adaptation_costs_rel=0.0, relative_abatement=0.0)
model1.save_simulation(sim_run1, "run_accreu_3_no_policy_no_adapt")


#### Run 4: no-policy baseline with optimal adaptation
params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
params["custom_constraints"]["constraint_variables"] = {"relative_abatement": 0}
model4 = MIMOSA(params)
model4.solve()
model4.save("run_accreu_4_no_policy_opt_adapt")


#### Run 5: Take a MIMOSA optimisation run and just change the adaptation level:

# Relative abatement is the only free variable in the model besides the adaptation level.
# By fixing this to the same values as in run 1, you obtain the same results in simulation
# mode, but now you can easily change the adaptation level
relative_abatement = model1.concrete_model.relative_abatement.extract_values()
sim_run5 = model1.run_simulation(
    relative_abatement=relative_abatement,
    slr_adaptation_costs_rel=0.00002,  # Example value
)
model1.save_simulation(sim_run5, "run_accreu_5_changed_adaptation")


# Plot the dependency graph for the equations and variables in the model:
model1.simulator.plot_dependency_graph()
