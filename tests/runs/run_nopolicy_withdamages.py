from mimosa import MIMOSA, load_params

params = load_params()

params["emissions"]["carbonbudget"] = False
params["economics"]["damages"]["ignore damages"] = False  # (1)!
params["model"]["welfare module"] = "cost_minimising"

# Force the mitigation effort to be zero
params["simulation"]["simulationmode"] = True
params["simulation"]["constraint_variables"] = {
    "relative_abatement": {
        year: {region: 0.0 for region in params["regions"]}
        for year in range(2025, 2151, 5)
    },
}
params["economics"]["MAC"]["gamma"] = "0.00001 USD2005/tCO2"  # (2)!

# Disable some emission reduction constraints
params["emissions"]["non increasing emissions after 2100"] = False
params["emissions"]["not positive after budget year"] = False
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["inertia"]["global"] = False

params["time"]["end"] = 2150

model = MIMOSA(params)
model.solve()
model.save("baseline_no_policy")
