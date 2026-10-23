from mimosa import MIMOSA, load_params


def test_initial_mitigation_level_is_fixed_at_zero():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}

    model = MIMOSA(params, prerun=False).concrete_model

    for region in model.regions:
        initial_abatement = model.mitigation_level[0, region]
        assert initial_abatement.fixed
        assert initial_abatement.value == 0
        assert not model.mitigation_level[1, region].fixed


def test_simulation_uses_fixed_initial_mitigation_level():
    params = load_params()
    params["time"]["end"] = 2030
    params["time"]["periods"] = {}

    model = MIMOSA(params, prerun=False)
    simulation = model.run_simulation(mitigation_level=0.5)
    assert "mitigation_level" in model.simulator.control_variables

    for region in model.concrete_model.regions:
        assert simulation.mitigation_level[0, region] == 0
        assert simulation.mitigation_level[1, region] == 0.5
