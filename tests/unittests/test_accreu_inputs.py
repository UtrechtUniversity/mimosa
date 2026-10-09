"""ACCREU inputs and options work without the abstract parameter data loader."""

from math import exp

import pytest
from pyomo.environ import value

from mimosa.common import ConcreteModel, Param, PyomoParam, Set, Var, quant
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.components.damages.accreu import all_damages, cge_damages
from mimosa.core.model_inputs import ModelInputs


def prepare_inputs(adaptation, determination, mortality, cge_quantile=None):
    settings = {
        "time": {"end": 2040, "periods": {2030: 10}},
        "model structure": {
            "damage module": "ACCREU",
        },
        "economics": {
            "damages": {
                "scale factor": 1.25,
                "accreu": {
                    "adaptation": adaptation,
                    "adaptation_determination": determination,
                    "adaptation_calibration": "literature_high",
                    "monetise_mortality": mortality,
                    "mortality_svl_rel_gdp_cap": 150,
                    "adaptation_effectiveness_scale_factor": 0.5,
                    "delay_adaptation_until_year": 2035,
                },
            }
        },
        "regions": {
            "USA": {
                "economics": {"gdp_ppp_2010_div_gdp_mer_2010": 2.5},
                "ACCREU": {
                    "labourprod_noadapt_ead_linear": 0.04,
                    "riverine_noadapt_ead_linear": 0.02,
                    "riverine_noadapt_ead_quadr": 0.01,
                    "slr_noadapt_ead_prod": 0.05,
                    "slr_noadapt_ead_power": 2,
                    "heat_related_mortality_perc_prod": 0.001,
                    "cold_related_mortality_perc_prod": -0.0005,
                    "labourprod_adapt_eff_max_effectiveness": 0.8,
                    "labourprod_adapt_eff_cost_param": 4,
                    "riverine_adapt_eff_max_effectiveness": 0.7,
                    "riverine_adapt_eff_cost_param": 3,
                    "slr_adapt_eff_max_effectiveness": 0.9,
                    "slr_adapt_eff_cost_param": 2,
                    "combined_adapt_eff_max_effectiveness": 0.65,
                    "combined_adapt_eff_cost_param": 5,
                },
            },
            "CAN": {},
        },
    }
    if cge_quantile is not None:
        settings["model structure"]["damage module"] = "ACCREU_CGE"
        settings["economics"]["damages"]["quantile"] = cge_quantile
        settings["regions"]["USA"]["ACCREU_CGE"] = {
            "NoSLR_b1": 1.0,
            "NoSLR_b2": 2.0,
            f"NoSLR_a{cge_quantile:.2f}": 3.0,
            "slr_b1": 4.0,
            "slr_b2": 5.0,
            f"slr_a{cge_quantile:.2f}": 6.0,
        }
    params, tree = check_params(settings, return_parser_tree=True)
    params = parse_param_values(params)
    return ModelInputs(
        params, tree, DataStore(params), RegionalParamStore(params, tree)
    )


def base_model(inputs):
    m = ConcreteModel()
    m.t = Set(initialize=inputs.t, ordered=True)
    m.regions = Set(initialize=inputs.regions, ordered=True)
    m.year = inputs.year
    m.baseline_GDP = Param(
        m.t,
        m.regions,
        initialize=inputs.time_regional("GDP"),
        units=quant.unit("currency_unit"),
    )
    m.population = Param(
        m.t,
        m.regions,
        initialize=inputs.time_regional("population"),
        units=quant.unit("billion people"),
    )
    m.gdp_ppp_2010_div_gdp_mer_2010 = Param(
        m.regions,
        initialize=inputs.regional("economics", "gdp_ppp_2010_div_gdp_mer_2010"),
    )
    m.dollar_2017_MER_to_2010_PPP = Param(
        m.regions, initialize=lambda m, r: 0.89632 * m.gdp_ppp_2010_div_gdp_mer_2010[r]
    )
    m.GDP_gross = Var(m.t, m.regions, initialize=lambda m, t, r: m.baseline_GDP[t, r])
    m.global_GDP_gross = Param(
        m.t, initialize=lambda m, t: sum(value(m.GDP_gross[t, r]) for r in m.regions)
    )
    m.T0 = Param(initialize=1.2, units=quant.unit("degC_above_PI"))
    m.temperature = Var(m.t, initialize={0: 1.2, 1: 2.0, 2: 3.0})
    m.total_SLR = Var(m.t, initialize={0: 0.1, 1: 0.3, 2: 0.6})
    return m


def check_regional_sources(m, inputs):
    for parameter in m.component_objects(PyomoParam):
        assert not callable(parameter.doc)
        if not str(parameter.doc).startswith("regional::ACCREU"):
            continue
        category, source = parameter.doc.split("::")[1].split(".", 1)
        for region in m.regions:
            assert value(parameter[region]) == pytest.approx(
                inputs.regional_store.getregional(category, source, region)
            )


@pytest.mark.parametrize("adaptation", ["noadaptation", "sectoral", "combined"])
@pytest.mark.parametrize("determination", ["solver_control", "analytical_optimum"])
@pytest.mark.parametrize("mortality", [False, True])
def test_native_accreu_parameters_options_bounds_and_equations(
    adaptation, determination, mortality
):
    inputs = prepare_inputs(adaptation, determination, mortality)
    m = base_model(inputs)
    equations = all_damages.get_constraints(m, inputs)
    rhs = {eq.lhs: eq for eq in equations if hasattr(eq, "lhs")}

    assert tuple(m.regions) == ("USA", "CAN")
    assert [m.year(t) for t in m.t] == [2025, 2030, 2040]
    assert value(m.damage_scale_factor) == 1.25
    assert value(m.mortality_svl_rel_gdp_per_cap) == 150
    assert (
        m.mortality_svl_rel_gdp_per_cap.doc
        == "::economics.damages.accreu.mortality_svl_rel_gdp_cap"
    )
    check_regional_sources(m, inputs)

    suffix = "" if adaptation == "noadaptation" else "_gross"
    expected_gross = {
        "labourprod": 1.25 * 0.04 * (2.0 - 1.2),
        "riverine": 1.25 * (0.02 * (2.0 - 1.2) + 0.01 * (2.0**2 - 1.2**2)),
        "slr": 1.25 * 0.05 * (0.3**2 - 0.1**2),
    }
    for sector, expected in expected_gross.items():
        name = sector + "_damage_costs" + suffix
        actual = value(rhs[name](m, 1, "USA"))
        assert actual == pytest.approx(expected)
        getattr(m, name)[1, "USA"].set_value(actual)
        assert value(rhs[name](m, 0, "USA")) == pytest.approx(0)

    assert hasattr(m, "adaptation_effectiveness_scale_factor") == (
        adaptation != "noadaptation"
    )
    assert hasattr(m, "combined_labprod_riv_adaptation_costs_abs") == (
        adaptation == "combined"
    )
    assert hasattr(m, "labourprod_adaptation_costs_abs") == (adaptation == "sectoral")
    if adaptation == "noadaptation":
        assert value(m.adaptation_costs_abs[1, "USA"]) == 0
        assert not hasattr(m, "delay_adaptation_year")
    else:
        assert value(m.adaptation_effectiveness_scale_factor) == 0.5
        assert value(m.delay_adaptation_year) == 2035
        # Independent literature_high factors and currency conversion.
        curves = {"slr": (0.9, 2, 0.933, 2)}
        if adaptation == "sectoral":
            curves.update(
                {"labourprod": (0.8, 4, 1.977, 0.5), "riverine": (0.7, 3, 0.721, 0.5)}
            )
        else:
            curves["combined_labprod_riv"] = (0.65, 5, 1.25, 0.25)
        for sector, (source_max, source_cost, max_scale, multiplier) in curves.items():
            cost_name = sector + "_adaptation_costs_abs"
            costs = getattr(m, cost_name)
            assert costs[1, "USA"].bounds == pytest.approx(
                (0, 0.1 * value(m.baseline_GDP[1, "USA"]))
            )
            costs[1, "USA"].set_value(0.01)
            expected = (
                source_max
                * max_scale
                * 0.5
                * (1 - exp(-source_cost / multiplier / (0.89632 * 2.5) * 0.01))
            )
            assert value(
                rhs[sector + "_avoided_damages_adapt"](m, 1, "USA")
            ) == pytest.approx(expected)
            assert (cost_name in rhs) == (determination == "analytical_optimum")
            if determination == "analytical_optimum":
                # Within the delay, the rule needs no gross-damage value.
                assert value(rhs[cost_name](m, 1, "USA")) == 0

    population = value(m.population[1, "USA"])
    heat = population * 0.001 * ((2.0 - 1.1) ** 2 - (1.2 - 1.1) ** 2)
    cold = population * -0.0005 * (2.0 - 1.2)
    assert value(rhs["mortality_heat_related"](m, 1, "USA")) == pytest.approx(heat)
    assert value(rhs["mortality_cold_related"](m, 1, "USA")) == pytest.approx(cold)
    assert hasattr(m, "mortality_svl") == mortality
    if mortality:
        m.mortality_heat_related[1, "USA"].set_value(heat)
        m.mortality_cold_related[1, "USA"].set_value(cold)
        vsl = 150 * value(m.GDP_gross[1, "USA"]) / population
        assert value(rhs["mortality_svl"](m, 1, "USA")) == pytest.approx(vsl)
        m.mortality_svl[1, "USA"].set_value(vsl)
        assert value(rhs["mortality_damage_costs_abs"](m, 1, "USA")) == pytest.approx(
            vsl * (heat + cold)
        )
        gdp = value(m.baseline_GDP[1, "USA"])
        assert m.mortality_damage_costs_abs[1, "USA"].bounds == pytest.approx(
            (-0.1 * gdp, 0.5 * gdp)
        )
    else:
        assert value(m.non_market_damage_costs_abs[1, "USA"]) == 0


@pytest.mark.parametrize("quantile", [0.05, 0.5, 0.95])
def test_native_cge_preserves_quantile_format_and_regional_overrides(quantile):
    inputs = prepare_inputs(
        "noadaptation", "solver_control", False, cge_quantile=quantile
    )
    m = base_model(inputs)
    equations = cge_damages.get_constraints(m, inputs)
    rhs = {eq.lhs: eq for eq in equations if hasattr(eq, "lhs")}
    check_regional_sources(m, inputs)
    assert m.damage_noslr_a.doc == f"regional::ACCREU_CGE.NoSLR_a{quantile:.2f}"
    assert m.damage_slr_a.doc == f"regional::ACCREU_CGE.slr_a{quantile:.2f}"
    x0, x = 1.2 - 0.85, 2.0 - 0.85
    expected = 1.25 * 3 * (x - x0 + 2 * (x**2 - x0**2)) / 100
    assert value(rhs["non_slr_damage_costs"](m, 1, "USA")) == pytest.approx(expected)
    expected_slr = 1.25 * 6 * (4 * (0.3 - 0.1) + 5 * (0.3**2 - 0.1**2)) / 100
    assert value(rhs["slr_damage_costs"](m, 1, "USA")) == pytest.approx(expected_slr)
    assert value(m.adaptation_costs_abs[1, "USA"]) == 0
