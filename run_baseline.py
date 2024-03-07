from mimosa import MIMOSA, load_params


for ignore_damages in [False]:
    params = load_params()
    params["emissions"]["carbonbudget"] = False
    params["model"]["welfare module"] = "cost_minimising"
    params["economics"]["MAC"]["gamma"] = "0.00001 USD2005/tCO2"
    params["simulation"]["simulationmode"] = True
    params["simulation"]["constraint_variables"] = {
        "relative_abatement": {
            year: {region: 0.0 for region in params["regions"]}
            for year in range(2025, 2151, 5)
        },
    }
    params["economics"]["damages"]["ignore damages"] = ignore_damages
    params["economics"]["damages"]["scale factor"] = 0.0 if ignore_damages else 1.0
    params["emissions"]["non increasing emissions after 2100"] = False
    params["emissions"]["not positive after budget year"] = False
    params["emissions"]["inertia"]["regional"] = False
    params["emissions"]["inertia"]["global"] = False

    params["time"]["end"] = 2150

    model = MIMOSA(params)
    model.solve(verbose=True)
    model.save(
        f"baseline3_ignore_damages_{ignore_damages}",
    )
