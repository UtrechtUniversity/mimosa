"""Migrated climate/mitigation declarations work without the abstract data loader."""

from math import log

import pytest
from pyomo.environ import value

from mimosa.common import AbstractModel, ConcreteModel, Param, Set, quant
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.components import emissions, mitigation, sealevelrise
from mimosa.core.model_inputs import ModelInputs


def make_inputs(pulse_year=2030, pulse_amount="1000 MtCO2"):
    params, tree = check_params(
        {
            "SSP": "SSP1",
            "regions": {
                "USA": {},
                "CAN": {"MAC": {"kappa_rel_abatement_0.4_2030": 0.7}},
            },
            "time": {"end": 2040, "periods": {2030: 10}},
            "emissions": {"pulse": {"year": pulse_year, "amount": pulse_amount}},
            "temperature": {"initial": "2 delta_degC", "TCRE": "0.75 delta_degC/TtCO2"},
            "economics": {"MAC": {
                "regional calibration factor": "kappa_rel_abatement_0.4_2030",
                "LBD_rate": 0.75, "LBD_scaling": "60 GtCO2", "LOT_rate": 0.02,
            }},
            "model structure": {"sealevelrise options": {"projection": "low"}},
        },
        return_parser_tree=True,
    )
    params = parse_param_values(params)
    inputs = ModelInputs(params, tree, DataStore(params), RegionalParamStore(params, tree))
    return inputs


@pytest.fixture(scope="module")
def inputs():
    return make_inputs()


def base_model(inputs, model_type=ConcreteModel):
    m = model_type()
    m.t = Set(initialize=inputs.t, ordered=True)
    m.regions = Set(initialize=inputs.regions, ordered=True)
    m.beginyear = Param(initialize=inputs.config("time.start"))
    m.tf = Param(initialize=len(inputs.t) - 1)
    m.period_length = Param(m.t, initialize=dict(enumerate(inputs.time_grid.period_lengths)))
    m.year = inputs.year
    m.ssp_baseline_emissions = Param(
        m.t, m.regions, initialize=inputs.time_regional("emissions"),
        units=quant.unit("emissionsrate_unit"),
    )
    m.baseline_GDP = Param(
        m.t, m.regions, initialize=inputs.time_regional("GDP"),
        units=quant.unit("currency_unit"),
    )
    return m


def test_emissions_initializes_quantities_flags_and_temperature_directly(inputs):
    m = base_model(inputs)
    emissions.get_constraints(m, inputs)

    assert value(m.emissions_pulse_year) == 2030
    assert value(m.emissions_pulse_amount) == pytest.approx(1.0)
    assert value(m.T0) == pytest.approx(2.0)
    assert value(m.TCRE) == pytest.approx(0.00075)
    assert value(m.budget) is False
    assert value(m.temperature_target) is False
    assert m.emissions_pulse_amount.doc == "::emissions.pulse.amount"
    assert m.T0.doc == "::temperature.initial"
    assert all(value(m.temperature[t]) == 2.0 for t in m.t)


def test_mitigation_owns_calibration_and_learning_inputs(inputs):
    m = base_model(inputs)
    emissions.get_constraints(m, inputs)
    assert not hasattr(m, "MAC_SSP_calibration_factor")
    mitigation.get_constraints(m, inputs)

    assert m.MAC_scaling_factor["CAN"] == 0.7
    assert m.MAC_scaling_factor.doc == "regional::MAC.kappa_rel_abatement_0.4_2030"
    assert m.MAC_SSP_calibration_factor.doc == "::economics.MAC.SSP_calibration_factor.SSP1"
    assert m.MAC_SSP_calibration_factor.extract_values() == pytest.approx(
        inputs.time_config("economics.MAC.SSP_calibration_factor.SSP1").values
    )
    assert value(m.LBD_rate) == 0.75
    assert value(m.LBD_scaling) == 60.0
    assert value(m.log_LBD_rate) == pytest.approx(log(0.75) / log(2))
    assert value(m.LOT_rate) == 0.02
    assert m.carbon_price[1, "CAN"].ub == pytest.approx(2 * value(m.MAC_gamma))


def test_slr_projection_comes_from_prepared_inputs(inputs):
    m = base_model(inputs)
    emissions.get_constraints(m, inputs)
    sealevelrise.get_constraints(m, inputs)

    assert value(m.slr_thermal_fast_sensitivity) == sealevelrise.SLR_PROJECTION_PARAMETER_SETS["low"]["thermal_fast_sensitivity"]
    assert value(m.slr_gsic_timescale) == sealevelrise.SLR_PROJECTION_PARAMETER_SETS["low"]["gsic_timescale"]
    assert value(m.slr_reference_year) == 1900
    assert value(m.slr_initial_year) == 2025


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("pulse_amount", ["1000 MtCO2", "-1 GtCO2"])
def test_pulse_validation_uses_initialized_values_in_both_model_types(model_type, pulse_amount):
    inputs = make_inputs(pulse_year=2032, pulse_amount=pulse_amount)
    m = base_model(inputs, model_type)
    with pytest.raises(ValueError, match="Emissions pulse year 2032 is not on the model time grid"):
        emissions.get_constraints(m, inputs)
        if model_type is AbstractModel:
            m.create_instance()


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
def test_zero_off_grid_pulse_remains_allowed(model_type):
    inputs = make_inputs(pulse_year=2032, pulse_amount="0 GtCO2")
    m = base_model(inputs, model_type)
    emissions.get_constraints(m, inputs)
    if model_type is AbstractModel:
        m = m.create_instance()
    assert value(m.emissions_pulse_amount) == 0
