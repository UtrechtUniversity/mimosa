"""Shared inputs and a small concrete model for policy-component tests."""

import pytest

from mimosa.common import ConcreteModel, Param, Set, Var
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.core.model_inputs import ModelInputs


def _make_policy_inputs(overrides=None):
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
    return inputs


def _make_policy_model(inputs):
    m = ConcreteModel()
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


@pytest.fixture
def policy_inputs():
    return _make_policy_inputs


@pytest.fixture
def policy_model():
    return _make_policy_model
