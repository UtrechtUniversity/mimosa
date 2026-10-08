"""Remaining sourced components work without abstract-model input hydration."""

from math import exp

import numpy as np
import pandas as pd
import pytest
from pyomo.environ import maximize, minimize, value

from mimosa.common import AbstractModel, ConcreteModel, Param, Set, Var, soft_min
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.components.effortsharing import equal_cumulative_per_cap, per_cap_convergence
from mimosa.components.emissiontrade import globalcostpool
from mimosa.components.objective import globalcosts, utility
from mimosa.components.welfare import cost_minimising, inequal_aversion_general
from mimosa.core.helpers import ModelContext
from mimosa.core.model_inputs import ModelInputs


def context(overrides=None):
    settings = {
        "time": {"end": 2050, "periods": {2030: 10}},
        "regions": {"USA": {}, "CAN": {}},
        "economics": {"elasmu": 1.4, "inequal_aversion": 0.2, "PRTP": 0.02},
        "effort sharing": {
            "percapconv_year": 2035,
            "ecpc_discount_rate": 0.05,
            "ecpc_start_year": 2010,
            "ecpc_repayment_endyear": 2045,
        },
    }
    if overrides:
        for section, values in overrides.items():
            settings[section].update(values)
    params, tree = check_params(settings, return_parser_tree=True)
    params = parse_param_values(params)
    inputs = ModelInputs(params, tree, DataStore(params), RegionalParamStore(params, tree))
    return ModelContext(components={}, inputs=inputs)


def base_model(context, model_type):
    inputs = context.inputs
    m = model_type()
    m.t = Set(initialize=inputs.t, ordered=True)
    m.regions = Set(initialize=inputs.regions, ordered=True)
    m.year = inputs.year
    m.beginyear = Param(initialize=inputs.config("time.start"))
    m.tf = Param(initialize=len(inputs.t) - 1)
    m.period_length = Param(m.t, initialize=dict(enumerate(inputs.time_grid.period_lengths)))
    m.population = Param(
        m.t, m.regions,
        initialize={(t, r): (3 + 0.5 * t if r == "USA" else 1 + 0.25 * t)
                    for t in inputs.t for r in inputs.regions},
    )
    m.global_population = Param(
        m.t, initialize=lambda m, t: sum(m.population[t, r] for r in m.regions)
    )
    m.consumption = Var(m.t, m.regions, initialize=lambda m, t, r: 12 if r == "USA" else 6)
    m.ssp_baseline_emissions = Param(
        m.t, m.regions, initialize=lambda m, t, r: 8 if r == "USA" else 2
    )
    m.GDP_gross = Var(m.t, m.regions, initialize=100)
    m.damage_costs = Param(m.t, m.regions, initialize=0.02)
    m.adaptation_costs = Param(m.t, m.regions, initialize=0.005)
    m.mitigation_costs_abs = Var(m.t, m.regions, initialize=5)
    return m


def constructed(m, model_type):
    return m.create_instance() if model_type is AbstractModel else m


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("component", [cost_minimising, inequal_aversion_general])
def test_remaining_welfare_parameters_and_nondefault_utility(model_type, component):
    ctx = context()
    m = base_model(ctx, model_type)
    equations = component.get_constraints(m, ctx)
    m = constructed(m, model_type)
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


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("component", [utility, globalcosts])
def test_objectives_initialize_prtp_and_preserve_discounting(model_type, component):
    ctx = context()
    m = base_model(ctx, model_type)
    m.global_welfare = Param(m.t, initialize=100)
    objective, constraints = component.get_constraints(m, ctx)
    m.objective = objective
    if component is globalcosts:
        m.cost_recurrence = constraints[0].to_pyomo_constraint(m)
    m = constructed(m, model_type)
    for t in m.t:
        m.NPV[t].set_value(10 * t)
    assert value(m.PRTP) == 0.02
    assert m.PRTP.doc == "::economics.PRTP"
    assert value(m.objective) == 30
    if component is utility:
        assert m.objective.sense == maximize
        assert value(constraints[0](m, 1)) == pytest.approx(5 * exp(-0.02 * 5) * 100)
    else:
        assert m.objective.sense == minimize
        cost = 2 * (5 + (0.02 + 0.005) * 100)
        assert value(m.cost_recurrence[1].body) == pytest.approx(10 - 5 * exp(-0.02 * 5) * cost)


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("year", [2025, 2035])
def test_convergence_uses_configured_year_for_derived_shares(model_type, year):
    ctx = context({"effort sharing": {"percapconv_year": year}})
    m = base_model(ctx, model_type)
    per_cap_convergence.get_constraints(m, ctx)
    m = constructed(m, model_type)
    assert value(m.percapconv_year) == year
    assert m.percapconv_year.doc == "::effort sharing.percapconv_year"
    for t in m.t:
        weight = 1 if year == 2025 else min((m.year(t) - 2025) / (year - 2025), 1)
        for region, initial_share in (("USA", 0.8), ("CAN", 0.2)):
            population_share = value(m.population[t, region]) / value(m.global_population[t])
            expected = weight * population_share + (1 - weight) * initial_share
            assert value(m.percapconv_share[t, region]) == pytest.approx(expected)


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("end_year", [2045, False])
def test_ecpc_nondefault_inputs_preserve_debt_and_discrete_repayment(
    monkeypatch, model_type, end_year
):
    years = [2010, 2015, 2020]
    emissions = pd.DataFrame({"USA": [8, 12, 15], "CAN": [2, 3, 5]}, index=years)
    population = pd.DataFrame({"USA": [2, 3, 4], "CAN": [1, 1, 1]}, index=years)
    monkeypatch.setattr(equal_cumulative_per_cap, "_load_data", lambda: (emissions, population))
    ctx = context({"effort sharing": {"ecpc_repayment_endyear": end_year}})
    m = base_model(ctx, model_type)
    equal_cumulative_per_cap.get_constraints(m, ctx)
    m = constructed(m, model_type)
    assert value(m.effortsharing_ecpc_discount_rate) == 0.05
    assert value(m.effortsharing_ecpc_start_year) == 2010
    assert value(m.effortsharing_ecpc_repayment_endyear) == end_year
    for name, path in (("discount_rate", "ecpc_discount_rate"), ("start_year", "ecpc_start_year"),
                       ("repayment_endyear", "ecpc_repayment_endyear")):
        assert getattr(m, "effortsharing_ecpc_" + name).doc == "::effort sharing." + path
    for region in m.regions:
        fair_share = population[region].to_numpy() / population.sum(axis=1).to_numpy() * emissions.sum(axis=1).to_numpy()
        debt = float(np.sum((emissions[region].to_numpy() - fair_share) * np.exp(-0.05 * (2025 - np.array(years)))))
        assert abs(debt) > 0
        assert value(m.effortsharing_ecpc_historical_debt[0, region]) == pytest.approx(debt)
        repayments = [value(m.effortsharing_ecpc_annual_debt_repayment[t, region]) for t in m.t]
        assert sum(repayments[t] * value(m.period_length[t]) for t in m.t) == pytest.approx(debt)
        if end_year is False:
            assert repayments == pytest.approx([debt / 25] * len(m.t))
        else:
            assert repayments[-1] == 0


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("enabled", [False, True])
def test_costpool_initializes_payment_limits_without_full_model_assembly(model_type, enabled):
    limits = {"min rel payment level": 0.2 if enabled else False,
              "max rel payment level": 1.5 if enabled else False}
    ctx = context({"economics": {"emission trade": limits}})
    m = base_model(ctx, model_type)
    globalcostpool.get_constraints(m, ctx)
    m = constructed(m, model_type)
    assert value(m.min_rel_payment_level) == limits["min rel payment level"]
    assert value(m.max_rel_payment_level) == limits["max rel payment level"]
    assert m.min_rel_payment_level.doc == "::economics.emission trade.min rel payment level"
    assert m.max_rel_payment_level.doc == "::economics.emission trade.max rel payment level"
