from mimosa import MIMOSA, load_params


def test_initial_relative_abatement_is_fixed_at_zero():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}

    model = MIMOSA(params, prerun=False).concrete_model

    for region in model.regions:
        initial_abatement = model.relative_abatement[0, region]
        assert initial_abatement.fixed
        assert initial_abatement.value == 0
        assert not model.relative_abatement[1, region].fixed


def test_simulation_uses_fixed_initial_relative_abatement():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}

    model = MIMOSA(params, prerun=False)
    simulation = model.run_simulation(relative_abatement=0.5)

    for region in model.concrete_model.regions:
        assert simulation.relative_abatement[0, region] == 0
        assert simulation.relative_abatement[1, region] == 0.5
