"""Welfare parameter metadata, configured utility and simulation behavior."""

import pytest
from pyomo.environ import ConcreteModel, Param, Set, Var, value

from mimosa import MIMOSA, load_params
from mimosa.common import soft_min
from mimosa.components.welfare import (
    cost_minimising,
    inequal_aversion_general,
    welfare_loss_minimising,
)
from mimosa.components.welfare.utility_fct import calc_utility
from mimosa.core.simulation.objects import SimulationObjectModel


@pytest.fixture(scope="module")
def welfare_model():
    params = load_params()
    params["time"].update(end=2030, periods={})
    params["regions"] = {"CAN": {}, "USA": {}}
    params["economics"]["elasmu"] = 1.4
    return MIMOSA(params, prerun=False)


def test_pipeline_supplies_inputs_using_existing_config_and_stores(welfare_model):
    preprocessor = welfare_model.preprocessor
    inputs = welfare_model.inputs

    assert welfare_model.inputs.config_value("model structure.welfare module") == "welfare_loss_minimising"
    assert inputs is preprocessor.inputs
    assert inputs.params is preprocessor.parsed_params
    assert inputs.parser_tree is preprocessor.parser_tree
    assert inputs.data_store is preprocessor._data_store
    assert inputs.regional_store is preprocessor._regional_param_store
    assert value(welfare_model.concrete_model.elasmu) == 1.4
    assert welfare_model.concrete_model.elasmu.doc == "::economics.elasmu"


def test_component_initializes_elasmu_from_prepared_inputs(welfare_model):
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1], ordered=True)
    model.regions = Set(initialize=["CAN", "USA"], ordered=True)
    model.year = welfare_model.inputs.year
    model.population = Param(model.t, model.regions, initialize=2.0)
    model.consumption = Var(model.t, model.regions, initialize=6.0)

    equations = welfare_loss_minimising.get_constraints(model, welfare_model.inputs)

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


def test_simulation_matches_its_utility_equations(welfare_model):
    simulation = welfare_model.run_simulation(relative_abatement=0.2)

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


@pytest.mark.parametrize("component", [cost_minimising, inequal_aversion_general])
def test_welfare_variants_use_configured_parameters_and_utility(
    component, policy_inputs, policy_model
):
    inputs = policy_inputs()
    m = policy_model(inputs)
    equations = component.get_constraints(m, inputs)
    assert value(m.elasmu) == 1.4
    assert m.elasmu.doc == "::economics.elasmu"
    if component is cost_minimising:
        expected = 4 * (value(soft_min(18 / 4)) ** (1 - 1.4) - 1) / (1 - 1.4)
    else:
        assert value(m.inequal_aversion) == 0.2
        assert m.inequal_aversion.doc == "::economics.inequal_aversion"
        total = 0
        for region in m.regions:
            pop = value(m.population[0, region])
            consumption = value(m.consumption[0, region])
            regional = pop * value(soft_min(consumption / pop)) ** (1 - 0.2)
            assert value(equations[0](m, 0, region)) == pytest.approx(regional)
            m.utility[0, region].set_value(regional)
            total += regional
        expected = 4 * value(soft_min(total / 4)) ** ((1 - 1.4) / (1 - 0.2)) / (1 - 1.4)
    assert value(equations[1](m, 0)) == pytest.approx(expected)
