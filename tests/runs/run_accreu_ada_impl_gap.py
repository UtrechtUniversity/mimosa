from mimosa import MIMOSA, load_params, load_adaptation_readiness

adaptation_readiness = load_adaptation_readiness()


def reduce_adaptation_costs(ssp, concrete_model):
    adaptation_vars = [
        "labourprod_adaptation_costs_abs",
        "slr_adaptation_costs_abs",
        "riverine_adaptation_costs_abs",
    ]

    # Keep the mitigation level (relative_abatement) the same
    control_values = {
        "relative_abatement": concrete_model.relative_abatement.extract_values()
    }

    def _get_adapt_readiness(t, r):
        year = str(int(concrete_model.year(t)))
        return adaptation_readiness.loc[(ssp, r), year]

    for adapt_var in adaptation_vars:
        values = getattr(concrete_model, adapt_var).extract_values()
        # Reduce these values by the adaptation readiness in each year/region
        reduced_values = {
            (t, r): _get_adapt_readiness(t, r) * value
            for (t, r), value in values.items()
        }
        control_values[adapt_var] = reduced_values

    return control_values


params = load_params()

params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"
params["economics"]["damages"]["accreu"][
    "adaptation_determination"
] = "analytical_optimum"

model_ada = MIMOSA(params)

# First run optimal adaptation simulation (ada)
sim_ada = model_ada.run_simulation()

# Then, calculate the reduced adaptation costs based on the adaptation readiness and the optimal adaptation simulation results
reduced_control_variables_values = reduce_adaptation_costs(params["SSP"], sim_ada)

# Finally, run the model again with these reduced adaptation costs, turning off analytical solution of optimal adaptation
params["economics"]["damages"]["accreu"]["adaptation_determination"] = "solver_control"
model = MIMOSA(params)
sim = model.run_simulation(**reduced_control_variables_values)

model.save_simulation(sim, "run_accreu_ada_impl_gap")
