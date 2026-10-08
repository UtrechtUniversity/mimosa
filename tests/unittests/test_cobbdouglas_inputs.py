"""Explicit economic inputs preserve initialization and production calibration."""

import pytest
from pyomo.environ import units, value

from mimosa import MIMOSA, load_params
from mimosa.common import ConcreteModel, Param, Set, quant
from mimosa.components import cobbdouglas


@pytest.fixture(scope="module")
def economic_model():
    params = load_params()
    params["time"].update(end=2040, periods={2030: 10})
    params["regions"] = {
        "USA": {"economics": {"init_capital_factor": 3.0}},
        "CAN": {"economics": {"init_capital_factor": 4.0}},
    }
    params["economics"]["GDP"].update(
        {"alpha": 0.35, "depreciation of capital": 0.06, "savings rate": 0.25}
    )
    return MIMOSA(params, prerun=False)


def build_component(inputs):
    model = ConcreteModel()
    model.t = Set(initialize=inputs.t, ordered=True)
    model.regions = Set(initialize=inputs.regions, ordered=True)
    model.year = inputs.year
    model.period_length = Param(
        model.t, initialize=dict(enumerate(inputs.time_grid.period_lengths))
    )
    model.baseline_GDP = Param(
        model.t, model.regions, initialize=inputs.time_regional("GDP"),
        units=quant.unit("currency_unit"),
    )
    model.population = Param(
        model.t, model.regions, initialize=inputs.time_regional("population"),
        units=quant.unit("billion people"),
    )
    model.global_baseline_GDP = Param(
        model.t, initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
    )
    cobbdouglas.get_constraints(model, inputs)
    return model


def check_capital_and_tfp(model):
    assert tuple(model.regions) == ("USA", "CAN")
    assert [value(model.period_length[t]) for t in model.t] == [0, 5, 10]
    assert value(model.alpha) == 0.35
    assert value(model.dk) == 0.06
    assert value(model.sr) == 0.25
    assert value(model.ignore_damages) is False
    assert str(units.get_units(model.init_capitalstock_factor)) == "dimensionless"
    assert str(units.get_units(model.capital_stock)) == str(quant.unit("currency_unit"))

    for region, factor in (("USA", 3.0), ("CAN", 4.0)):
        assert value(model.init_capitalstock_factor[region]) == factor
        capital = factor * value(model.baseline_GDP[0, region])
        for t in model.t:
            gdp = value(model.baseline_GDP[t, region])
            population = value(model.population[t, region])
            if t > 0:
                dt = value(model.period_length[t])
                capital = (1 - 0.06) ** dt * capital + 0.25 * value(
                    model.baseline_GDP[t - 1, region]
                ) * dt
            expected_tfp = gdp / (population ** (1 - 0.35) * capital ** 0.35)
            assert value(model.TFP[t, region]) == pytest.approx(expected_tfp, rel=1e-12)
            assert value(model.capital_stock[t, region]) == pytest.approx(factor * gdp)


def test_economic_component_initializes_inputs_without_abstract_loader(economic_model):
    model = build_component(economic_model.inputs)
    check_capital_and_tfp(model)
    assert model.init_capitalstock_factor.doc == "regional::economics.init_capital_factor"
    assert model.alpha.doc == "::economics.GDP.alpha"
    assert model.dk.doc == "::economics.GDP.depreciation of capital"
    assert model.sr.doc == "::economics.GDP.savings rate"
    assert model.ignore_damages.doc == "::economics.damages.ignore damages"


def test_abstract_pipeline_keeps_overrides_initialization_and_tfp(economic_model):
    check_capital_and_tfp(economic_model.concrete_model)


def test_economic_simulation_uses_configured_production_and_savings(economic_model):
    simulation = economic_model.run_simulation()
    model = economic_model.concrete_model
    for t in model.t:
        for region in model.regions:
            # The production equation deliberately smooths capital with soft_min.
            capital = simulation.capital_stock[t, region]
            expected_gdp = (
                value(model.baseline_GDP[0, region]) if t == 0 else
                value(model.TFP[t, region])
                * simulation.population[t, region] ** (1 - 0.35)
                * value(cobbdouglas.soft_min(capital, scale=10)) ** 0.35
            )
            assert simulation.GDP_gross[t, region] == pytest.approx(expected_gdp)
            assert simulation.investments[t, region] == pytest.approx(
                0.25 * simulation.GDP_net[t, region]
            )
