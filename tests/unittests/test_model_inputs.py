"""Input lookup agrees with the current model's data-loading semantics."""

from copy import deepcopy

import numpy as np
import pytest
from pyomo.environ import value

from mimosa import MIMOSA
from mimosa.common import Any, ConcreteModel, Param, Set, SourcedValue, quant
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.core.model_inputs import ModelInputs


def prepare(overrides=None):
    params, parser_tree = check_params(
        {} if overrides is None else overrides, return_parser_tree=True
    )
    params = parse_param_values(params)
    return params, parser_tree


def make_inputs(params, parser_tree):
    return ModelInputs(
        params=params,
        parser_tree=parser_tree,
        data_store=DataStore(params),
        regional_store=RegionalParamStore(params, parser_tree),
    )


@pytest.fixture(scope="module")
def inputs():
    params, parser_tree = prepare(
        {
            "SSP": "SSP1",
            "time": {"end": 2060, "periods": {2050: 10}},
            "regions": {
                "USA": None,
                "CAN": {"economics": {"init_capital_factor": 4.0}},
            },
            "emissions": {"pulse": {"year": 2030, "amount": "1000 MtCO2"}},
        }
    )
    return make_inputs(params, parser_tree)


def test_config_scalar_quantities_and_false_keep_values_and_metadata(inputs):
    alpha = inputs.config("economics.GDP.alpha")
    assert isinstance(alpha, SourcedValue)
    assert alpha.values == 0.3
    assert alpha.documentation_key == "::economics.GDP.alpha"
    assert inputs.config_value("economics.GDP.alpha") == alpha.values
    assert inputs.config("emissions.pulse.amount").values == pytest.approx(1.0)
    assert inputs.config("economics.MAC.gamma").values == pytest.approx(
        quant("2887 USD2010/tCO2", "currency_unit/emissionsrate_unit")
    )
    assert inputs.config("temperature.TCRE").values == pytest.approx(
        quant("0.62 delta_degC/(TtCO2)", "temperature_unit/emissions_unit")
    )
    assert inputs.config("emissions.carbonbudget").values is False
    assert inputs.config_value("temperature.target") is False


def test_sections_dictionary_settings_and_nested_regional_values_are_plain(inputs):
    before = deepcopy(inputs.params)
    options = inputs.config_value("economics.damages.accreu")
    assert options == inputs.params["economics"]["damages"]["accreu"]
    assert options["adaptation"] == "separate"
    assert inputs.config_value("model structure.damage module") == "COACCH"
    assert inputs.config_value("economics.MAC")["gamma"] == "2887 USD2010/tCO2"
    frames = inputs.config("economics.MAC.SSP_calibration_factor.SSP1")
    assert frames.values == {2020.0: 1.0, 2100.0: 0.618}
    assert inputs.config_value("regions.CAN.economics.init_capital_factor") == 4.0
    assert inputs.config_value("regions.USA") == {}
    assert inputs.params == before


@pytest.mark.parametrize(
    "path", ["missing", "economics.missing", "economics.GDP.alpha.child", ""]
)
def test_missing_config_paths_have_context(inputs, path):
    with pytest.raises(KeyError, match="Configuration path") as error:
        inputs.config(path)
    assert repr(path) in str(error.value)


def test_grid_and_regions_keep_model_index_order(inputs):
    assert tuple(inputs.t) == tuple(range(7))
    assert inputs.regions == ("USA", "CAN")
    assert inputs.time_grid.years == (2025, 2030, 2035, 2040, 2045, 2050, 2060)
    assert inputs.time_grid.period_lengths == (0, 5, 5, 5, 5, 5, 10)
    assert [inputs.year(t) for t in inputs.t] == list(inputs.time_grid.years)
    assert isinstance(inputs.year(0), np.floating)


def test_regional_lookup_preserves_override_and_dynamic_source_key(inputs):
    capital = inputs.regional("economics", "init_capital_factor")
    assert tuple(capital.values) == inputs.regions
    assert capital.values["CAN"] == 4.0
    assert capital.values["USA"] == inputs.regional_store.getregional(
        "economics", "init_capital_factor", "USA"
    )
    assert capital.documentation_key == "regional::economics.init_capital_factor"
    calibration = inputs.config_value("economics.MAC.regional calibration factor")
    source = inputs.regional("MAC", calibration)
    assert source.documentation_key == f"regional::MAC.{calibration}"
    assert all(np.isfinite(number) for number in source.values.values())


@pytest.mark.parametrize("category,name", [("missing", "factor"), ("economics", "missing")])
def test_missing_regional_inputs_have_context(inputs, category, name):
    with pytest.raises(KeyError, match="Regional input") as error:
        inputs.regional(category, name)
    assert f"{category}.{name}" in str(error.value)


def test_missing_time_regional_input_has_context(inputs):
    with pytest.raises(KeyError, match="Time-and-region input 'missing'"):
        inputs.time_regional("missing")


def test_regional_string_data_retains_values_and_native_any_domain(inputs):
    source = inputs.regional("COACCH", "NoSLR_form")
    model = ConcreteModel()
    model.regions = Set(initialize=inputs.regions, ordered=True)
    model.damage_form = Param(model.regions, initialize=source, within=Any)

    assert all(isinstance(form, str) for form in source.values.values())
    assert model.damage_form.extract_values() == source.values
    assert model.damage_form.doc == "regional::COACCH.NoSLR_form"


@pytest.mark.parametrize("name", ["population", "GDP", "emissions"])
def test_time_regional_data_keeps_full_grid_and_region_dimensions(inputs, name):
    source = inputs.time_regional(name)
    indices = [(t, r) for t in inputs.t for r in inputs.regions]
    assert list(source.values) == indices
    assert source.documentation_key == f"timeandregional::{name}"
    for t, r in indices:
        assert source.values[t, r] == pytest.approx(
            inputs.data_store.interp_data(inputs.year(t), r, name), rel=1e-12
        )


def test_time_config_interpolates_the_explicitly_selected_path(inputs):
    ssp = inputs.config_value("SSP")
    source = inputs.time_config(f"economics.MAC.SSP_calibration_factor.{ssp}")
    assert source.documentation_key == "::economics.MAC.SSP_calibration_factor.SSP1"
    assert list(source.values) == list(inputs.t)
    assert source.values[0] == pytest.approx(1 - (2025 - 2020) / 80 * (1 - 0.618))
    assert source.values[6] == pytest.approx(1 - (2060 - 2020) / 80 * (1 - 0.618))
    # The caller selects the path; lookup does not impose the configured SSP.
    assert inputs.time_config("economics.MAC.SSP_calibration_factor.SSP2").values == {
        t: 1.0 for t in inputs.t
    }


def test_lookup_values_construct_native_pyomo_parameters_and_derived_values(inputs):
    model = ConcreteModel()
    model.t = Set(initialize=inputs.t, ordered=True)
    model.regions = Set(initialize=inputs.regions, ordered=True)
    model.alpha = Param(initialize=inputs.config("economics.GDP.alpha"))
    model.capital_factor = Param(
        model.regions, initialize=inputs.regional("economics", "init_capital_factor")
    )
    model.population = Param(
        model.t, model.regions,
        initialize=inputs.time_regional("population"), units=quant.unit("billion people"),
    )
    model.global_population = Param(
        model.t, initialize=lambda m, t: sum(m.population[t, r] for r in m.regions),
        units=quant.unit("billion people"),
    )
    calibration = inputs.time_config("economics.MAC.SSP_calibration_factor.SSP1")
    model.mac_factor = Param(model.t, initialize=calibration)
    population = inputs.time_regional("population").values

    assert value(model.alpha) == 0.3
    assert model.alpha.doc == "::economics.GDP.alpha"
    assert model.capital_factor["CAN"] == 4.0
    for t in inputs.t:
        assert value(model.global_population[t]) == pytest.approx(
            sum(population[t, r] for r in inputs.regions)
        )
    assert model.population.doc == "timeandregional::population"
    assert model.population.index_set().dimen == 2
    assert model.mac_factor.extract_values() == calibration.values
    assert model.mac_factor.doc == calibration.documentation_key


def test_lookup_matches_current_model_initialization(inputs):
    model = MIMOSA(deepcopy(inputs.params), prerun=False).concrete_model
    assert [model.year(t) for t in model.t] == [inputs.year(t) for t in inputs.t]
    assert tuple(model.regions) == inputs.regions
    for path, name in (
        ("economics.GDP.alpha", "alpha"),
        ("economics.MAC.gamma", "MAC_gamma"),
        ("temperature.TCRE", "TCRE"),
        ("emissions.pulse.amount", "emissions_pulse_amount"),
    ):
        assert value(getattr(model, name)) == pytest.approx(inputs.config_value(path))
    assert value(model.budget) is inputs.config_value("emissions.carbonbudget")
    for source_name, parameter_name in (
        ("population", "population"), ("GDP", "baseline_GDP"),
        ("emissions", "ssp_baseline_emissions"),
    ):
        assert getattr(model, parameter_name).extract_values() == pytest.approx(
            inputs.time_regional(source_name).values, rel=1e-12
        )
    assert model.init_capitalstock_factor.extract_values() == pytest.approx(
        inputs.regional("economics", "init_capital_factor").values
    )
    assert model.MAC_SSP_calibration_factor.extract_values() == pytest.approx(
        inputs.time_config("economics.MAC.SSP_calibration_factor.SSP1").values
    )


@pytest.mark.parametrize("amount", ["1000 MtCO2", "-1 GtCO2"])
def test_lookup_does_not_apply_emissions_specific_pulse_validation(inputs, amount):
    params, tree = prepare({"emissions": {"pulse": {"year": 2032, "amount": amount}}})
    lookup = ModelInputs(params, tree, inputs.data_store, inputs.regional_store)
    assert lookup.config_value("emissions.pulse.year") == 2032
    assert abs(lookup.config_value("emissions.pulse.amount")) == 1.0


def test_zero_off_grid_pulse_is_allowed(inputs):
    params, tree = prepare({"emissions": {"pulse": {"year": 2032, "amount": "0 GtCO2"}}})
    lookup = make_inputs(params, tree)
    assert lookup.config_value("emissions.pulse.amount") == 0


def test_fractional_grid_and_single_region_have_correct_indices():
    params, tree = prepare(
        {"time": {"end": 2035, "dt": 2.5, "periods": {}}, "regions": {"CAN": None}}
    )
    lookup = make_inputs(params, tree)
    assert lookup.time_grid.years == (2025, 2027.5, 2030, 2032.5, 2035)
    assert lookup.time_grid.period_lengths == (0, 2.5, 2.5, 2.5, 2.5)
    assert list(lookup.time_regional("population").values) == [(t, "CAN") for t in range(5)]


def test_time_config_clamps_before_and_after_keyframe_range():
    params, tree = prepare(
        {
            "regions": {"CAN": None},
            "time": {"end": 2050, "periods": {}},
            "economics": {"MAC": {"SSP_calibration_factor": {"SSP2": {2030: 2, 2040: 4}}}},
        }
    )
    lookup = make_inputs(params, tree)
    assert lookup.time_config("economics.MAC.SSP_calibration_factor.SSP2").values == {
        0: 2, 1: 2, 2: 3, 3: 4, 4: 4, 5: 4
    }


def test_time_config_accepts_non_mac_config_with_calendar_keys():
    params, tree = prepare(
        {
            "regions": {"CAN": None},
            "time": {"end": 2050, "periods": {2030: 5, 2040: 10}},
        }
    )
    lookup = make_inputs(params, tree)
    source = lookup.time_config("time.periods")

    assert lookup.time_grid.years == (2025, 2030, 2035, 2040, 2050)
    assert source.values == {0: 5, 1: 5, 2: 7.5, 3: 10, 4: 10}
    assert source.documentation_key == "::time.periods"


@pytest.mark.parametrize(
    "path", ["economics.GDP.alpha", "model structure.damage module", "time.periods"]
)
def test_time_config_requires_nonempty_keyframe_mapping(inputs, path):
    params, tree = prepare({"time": {"periods": {}}})
    lookup = ModelInputs(params, tree, inputs.data_store, inputs.regional_store)
    with pytest.raises(ValueError, match="must be a non-empty year-to-value mapping"):
        lookup.time_config(path)


def test_time_config_rejects_nonnumeric_keyframes_with_path_context(inputs):
    path = "economics.damages.accreu"
    with pytest.raises(ValueError, match="must map numeric calendar years") as error:
        inputs.time_config(path)
    assert path in str(error.value)


def test_time_config_reports_missing_configuration_path(inputs):
    with pytest.raises(KeyError, match="Configuration path 'missing'"):
        inputs.time_config("missing")


def test_invalid_grid_reuses_existing_validation(inputs):
    params, tree = prepare({"time": {"end": 2051}})
    with pytest.raises(ValueError, match="time.end 2051 is not reachable"):
        ModelInputs(params, tree, inputs.data_store, inputs.regional_store)
