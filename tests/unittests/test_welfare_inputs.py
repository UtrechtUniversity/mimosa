"""The welfare-loss pilot works with explicit inputs and the current pipeline."""

import pytest
from pyomo.environ import ConcreteModel, Param, Set, Var, value

from mimosa import MIMOSA, load_params
from mimosa.components.welfare import welfare_loss_minimising
from mimosa.components.welfare.utility_fct import calc_utility
from mimosa.core.simulation.objects import SimulationObjectModel


@pytest.fixture(scope="module")
def pilot():
    params = load_params()
    params["time"].update(end=2030, periods={})
    params["regions"] = {"CAN": {}, "USA": {}}
    params["economics"]["elasmu"] = 1.4
    return MIMOSA(params, prerun=False)


def test_pipeline_supplies_inputs_using_existing_config_and_stores(pilot):
    preprocessor = pilot.preprocessor
    inputs = pilot.model_context.inputs

    assert pilot.model_context.module("welfare") == "welfare_loss_minimising"
    assert inputs is preprocessor.inputs
    assert inputs.params is preprocessor.parsed_params
    assert inputs.parser_tree is preprocessor.parser_tree
    assert inputs.data_store is preprocessor._data_store
    assert inputs.regional_store is preprocessor._regional_param_store
    assert value(pilot.concrete_model.elasmu) == 1.4
    assert pilot.concrete_model.elasmu.doc == "::economics.elasmu"


def test_component_initializes_elasmu_without_the_abstract_data_loader(pilot):
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.regions = Set(initialize=["CAN", "USA"], ordered=True)
    model.year = pilot.model_context.inputs.year
    model.population = Param(model.t, model.regions, initialize=2.0)
    model.consumption = Var(model.t, model.regions, initialize=6.0)

    equations = welfare_loss_minimising.get_constraints(model, pilot.model_context)

    assert value(model.elasmu) == 1.4
    assert model.elasmu.doc == "::economics.elasmu"
    assert [equation.name for equation in equations] == ["utility", "global_welfare"]
    regional_utility = value(equations[0](model, 1, "CAN"))
    assert regional_utility == pytest.approx(calc_utility(6.0, 2.0, 1.4))
    for region in model.regions:
        model.utility[1, region].set_value(regional_utility)
    assert value(equations[1](model, 1)) == pytest.approx(4.0 * regional_utility)

    simulation = SimulationObjectModel(model)
    assert equations[0](simulation, 1, "CAN") == pytest.approx(regional_utility)
    assert equations[1](simulation, 1) == pytest.approx(4.0 * regional_utility)


def test_pilot_simulation_matches_its_utility_equations(pilot):
    simulation = pilot.run_simulation(relative_abatement=0.2)

    for t in simulation.t:
        expected_welfare = 0.0
        for region in simulation.regions:
            utility = calc_utility(
                simulation.consumption[t, region],
                simulation.population[t, region],
                1.4,
            )
            assert simulation.utility[t, region] == pytest.approx(utility)
            expected_welfare += simulation.population[t, region] * utility
        assert simulation.global_welfare[t] == pytest.approx(expected_welfare)
