from mimosa import MIMOSA, load_params

params = load_params()

params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"
params["economics"]["damages"]["accreu"][
    "adaptation_determination"
] = "analytical_optimum"


# First run optimal adaptation simulation (ada)
model_ada = MIMOSA(params)
sim_ada = model_ada.run_simulation()

# Then, reduce the adaptation effectiveness, turning off analytical solution of optimal adaptation
params["economics"]["damages"]["accreu"]["adaptation_effectiveness_scale_factor"] = 0.5
params["economics"]["damages"]["accreu"]["adaptation_determination"] = "solver_control"

# And run the model with the same control variable values as the optimal adaptation simulation,
# but with reduced adaptation effectiveness
model = MIMOSA(params)
control_variables = model.simulator.control_variables
control_variables_values = {
    var: getattr(sim_ada, var).extract_values() for var in control_variables
}
sim = model.run_simulation(**control_variables_values)

model.save_simulation(sim, "run_accreu_ada_red_eff")
