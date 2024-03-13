from mimosa import MIMOSA, load_params


for ignore_damages in [False, True]:
    params = load_params()
    params["emissions"]["carbonbudget"] = False
    params["economics"]["damages"]["ignore damages"] = ignore_damages
    params["model"]["welfare module"] = "cost_minimising"

    if not ignore_damages:
        params["simulation"]["simulationmode"] = True
        params["simulation"]["constraint_variables"] = {
            "relative_abatement": {
                year: {region: 0.0 for region in params["regions"]}
                for year in range(2025, 2151, 5)
            },
        }
        params["economics"]["MAC"]["gamma"] = "0.00001 USD2005/tCO2"

    # Disable
    params["emissions"]["non increasing emissions after 2100"] = False
    params["emissions"]["not positive after budget year"] = False
    params["emissions"]["inertia"]["regional"] = False
    params["emissions"]["inertia"]["global"] = False

    params["time"]["end"] = 2150

    model = MIMOSA(params)
    model.solve(verbose=True)
    model.save(
        f"baseline_ignore_damages_{ignore_damages}",
    )
