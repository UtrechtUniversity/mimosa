from mimosa import MIMOSA, load_params

#### Run "mit_ada" (Tier 1): CBA with adaptation optimised by MIMOSA

params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
model_mit_ada = MIMOSA(params)
# Plot the dependency graph for the equations and variables in the model:
# model1.simulator.plot_dependency_graph()
model_mit_ada.solve()
model_mit_ada.save("run_accreu_tier1_mit_ada")

#### Run "mit" (Tier 1): CBA with no adaptation

params = load_params()
params["emissions"]["carbonbudget"] = False
params["model"]["damage module"] = "ACCREU"
params["custom_constraints"]["constraint_variables"] = {"slr_avoided_damages": 0}
model_mit = MIMOSA(params)
model_mit.solve()
model_mit.save("run_accreu_tier1_mit")


#### Run "ada" (Tier 1): no-policy baseline with optimal adaptation
params_ada = load_params()
params_ada["emissions"]["carbonbudget"] = False
params_ada["model"]["damage module"] = "ACCREU"
params_ada["custom_constraints"]["constraint_variables"] = {"carbonprice": 0}
model_ada = MIMOSA(params_ada)
model_ada.solve()
model_ada.save("run_accreu_tier1_ada")


#### Run "baseline" (Tier 1): no-policy baseline with no adaptation
params = load_params()
params["model"]["damage module"] = "ACCREU"
model_baseline = MIMOSA(params)

relative_abatement_ada = model_ada.concrete_model.relative_abatement.extract_values()
sim_run_baseline = model_baseline.run_simulation(
    slr_adaptation_costs_rel=0.0, relative_abatement=relative_abatement_ada
)
model_baseline.save_simulation(sim_run_baseline, "run_accreu_tier1_baseline")


#### Run "mit_ada_unplanned" (Tier 2): Take a MIMOSA optimisation run and just change the adaptation level:

# Relative abatement is the only free variable in the model besides the adaptation level.
# By fixing this to the same values as in run 1, you obtain the same results in simulation
# mode, but now you can easily change the adaptation level

params_mit_ada_unplanned = load_params()
params_mit_ada_unplanned["emissions"]["carbonbudget"] = False
params_mit_ada_unplanned["model"]["damage module"] = "ACCREU"
params_mit_ada_unplanned["economics"]["adaptation"]["slr_effectiveness_limit"] = 0.5
model_mit_ada_unplanned = MIMOSA(params_mit_ada_unplanned)

relative_abatement = model_mit_ada.concrete_model.relative_abatement.extract_values()
slr_adaptation_costs_rel = (
    model_mit_ada.concrete_model.slr_adaptation_costs_rel.extract_values()
)
sim_run_ada_unplanned = model_mit_ada_unplanned.run_simulation(
    relative_abatement=relative_abatement,
    slr_adaptation_costs_rel=slr_adaptation_costs_rel,
)
model_mit_ada_unplanned.save_simulation(
    sim_run_ada_unplanned, "run_accreu_tier2_mit_ada_unplanned"
)


#### Run "first_opt_mit_then_opt_adapt" (Tier 4): Given mitigation from run 2a, optimise adaptation

params_first_mit_then_adapt = load_params()
params_first_mit_then_adapt["emissions"]["carbonbudget"] = False
params_first_mit_then_adapt["model"]["damage module"] = "ACCREU"
params_first_mit_then_adapt["custom_constraints"]["constraint_variables"] = {
    "relative_abatement": "output/run_accreu_tier1_mit.csv"
}
model_first_mit_then_adapt = MIMOSA(params_first_mit_then_adapt)
model_first_mit_then_adapt.solve()
model_first_mit_then_adapt.save("run_accreu_tier4_first_opt_mit_then_opt_adapt")
