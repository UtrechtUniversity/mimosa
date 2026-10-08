"""COACCH chooses its own inputs in both native and production construction."""

from math import isnan

import pytest
from pyomo.environ import value

from mimosa import MIMOSA
from mimosa.common import AbstractModel, Any, ConcreteModel, Param, Set, Var, quant
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.components.damages import coacch
from mimosa.core.helpers import ModelContext
from mimosa.core.model_inputs import ModelInputs


def config(combined, adaptation, quantile):
    prefix = "Ad" if adaptation else "NoAd"
    return {
        "time": {"end": 2040, "periods": {2030: 10}},
        "economics": {"damages": {
            "scale factor": 1.25,
            "quantile": quantile,
            "coacch_combined_slr_nonslr_damages": combined,
            "coacch_slr_withadapt": adaptation,
        }},
        "regions": {
            "USA": {"COACCH": {
                "NoSLR_form": "Robust-Quadratic",
                "NoSLR_b1": 1.0,
                "NoSLR_b2": 2.0,
                "NoSLR_b3": float("nan"),
                f"NoSLR_a (q={quantile})": 2.0,
                f"combined_b1_{prefix}-q{quantile}": 4.0,
                f"combined_b2_{prefix}-q{quantile}": 6.0,
                f"SLR-{prefix}_form": "Robust-Linear",
                f"SLR-{prefix}_b1": 8.0,
                f"SLR-{prefix}_b2": float("nan"),
                f"SLR-{prefix}_b3": float("nan"),
                f"SLR-{prefix}_a (q={quantile})": 3.0,
            }},
            "CAN": {},
        },
    }


def prepare_inputs(settings):
    params, tree = check_params(settings, return_parser_tree=True)
    params = parse_param_values(params)
    return ModelInputs(params, tree, DataStore(params), RegionalParamStore(params, tree))


def check_selected_parameters(m, store, combined, adaptation, quantile):
    prefix = "Ad" if adaptation else "NoAd"
    assert tuple(m.regions) == ("USA", "CAN")
    assert value(m.damage_scale_factor) == 1.25
    assert m.damage_scale_factor.doc == "::economics.damages.scale factor"
    for name in ("damage_noslr_form", "damage_noslr_b3", "damage_slr_form",
                 "damage_slr_b2", "damage_slr_b3"):
        assert getattr(m, name).domain is Any

    if combined:
        for region in m.regions:
            assert value(m.damage_noslr_form[region]) == "Robust-Quadratic"
            assert value(m.damage_noslr_b3[region]) == 0
            assert value(m.damage_noslr_a[region]) == 1
            assert value(m.damage_slr_form[region]) == "Robust-Linear"
            for suffix in ("b1", "b2", "b3", "a"):
                assert value(getattr(m, "damage_slr_" + suffix)[region]) == 0
        for suffix in ("b1", "b2"):
            parameter = getattr(m, "damage_noslr_" + suffix)
            source = f"combined_{suffix}_{prefix}-q{quantile}"
            assert parameter.doc == "regional::COACCH." + source
            for region in m.regions:
                assert value(parameter[region]) == store.getregional("COACCH", source, region)
        for name in ("damage_noslr_form", "damage_noslr_b3", "damage_noslr_a",
                     "damage_slr_form", "damage_slr_b1", "damage_slr_b2",
                     "damage_slr_b3", "damage_slr_a"):
            assert getattr(m, name).doc is None
    else:
        for group, source_prefix in (("noslr", "NoSLR"), ("slr", f"SLR-{prefix}")):
            for suffix in ("form", "b1", "b2", "b3", "a"):
                parameter = getattr(m, f"damage_{group}_{suffix}")
                source = f"{source_prefix}_{suffix}"
                if suffix == "a":
                    source += f" (q={quantile})"
                assert parameter.doc == "regional::COACCH." + source
                for region in m.regions:
                    expected = store.getregional("COACCH", source, region)
                    if isinstance(expected, float) and isnan(expected):
                        assert isnan(value(parameter[region]))
                    else:
                        assert value(parameter[region]) == expected


@pytest.mark.parametrize("model_type", [AbstractModel, ConcreteModel])
@pytest.mark.parametrize("combined", [False, True])
@pytest.mark.parametrize("adaptation", [False, True])
@pytest.mark.parametrize("quantile", [0.025, 0.5, 0.975])
def test_native_construction_selects_only_needed_sources(
    monkeypatch, model_type, combined, adaptation, quantile
):
    inputs = prepare_inputs(config(combined, adaptation, quantile))
    prefix = "Ad" if adaptation else "NoAd"
    allowed = (
        {f"combined_b1_{prefix}-q{quantile}", f"combined_b2_{prefix}-q{quantile}"}
        if combined else
        {"NoSLR_form", "NoSLR_b1", "NoSLR_b2", "NoSLR_b3", f"NoSLR_a (q={quantile})",
         f"SLR-{prefix}_form", f"SLR-{prefix}_b1", f"SLR-{prefix}_b2",
         f"SLR-{prefix}_b3", f"SLR-{prefix}_a (q={quantile})"}
    )
    calls = []
    get = inputs.regional_store.get

    def selected_get(category, name):
        assert category == "COACCH"
        assert name in allowed, f"Unneeded damage source requested: {name}"
        calls.append(name)
        return get(category, name)

    monkeypatch.setattr(inputs.regional_store, "get", selected_get)
    m = model_type()
    m.t = Set(initialize=inputs.t, ordered=True)
    m.regions = Set(initialize=inputs.regions, ordered=True)
    m.T0 = Param(initialize=1.2, units=quant.unit("degC_above_PI"))
    m.temperature = Var(m.t, initialize={0: 1.2, 1: 2.0, 2: 3.0})
    m.total_SLR = Var(m.t, initialize={0: 0.1, 1: 0.3, 2: 0.6})
    equations = coacch.get_constraints(m, ModelContext(components={}, inputs=inputs))
    if model_type is AbstractModel:
        m = m.create_instance()

    assert set(calls) == allowed
    assert len(calls) == len(allowed)
    check_selected_parameters(m, inputs.regional_store, combined, adaptation, quantile)
    temperature_equation = next(eq for eq in equations if eq.lhs == "non_slr_damage_costs")
    slr_equation = next(eq for eq in equations if eq.lhs == "slr_damage_costs")
    x0, x = 1.2 - 0.6, 2.0 - 0.6
    b1, b2, a = (4.0, 6.0, 1.0) if combined else (1.0, 2.0, 2.0)
    expected = 1.25 * a * (b1 * (x - x0) + b2 * (x**2 - x0**2)) / 100
    assert value(temperature_equation(m, 1, "USA")) == pytest.approx(expected)
    expected_slr = 0 if combined else 1.25 * 3 * 8 * (0.3 - 0.1) / 100
    assert value(slr_equation(m, 1, "USA")) == pytest.approx(expected_slr)
    assert value(temperature_equation(m, 0, "USA")) == pytest.approx(0)
    assert value(slr_equation(m, 0, "USA")) == pytest.approx(0)
    assert m.slr_damage_costs[1, "USA"].bounds == (-0.5, 0.7)


@pytest.mark.parametrize("combined", [False, True])
@pytest.mark.parametrize("adaptation", [False, True])
def test_production_pipeline_preserves_selected_overrides(
    monkeypatch, combined, adaptation
):
    get = RegionalParamStore.get

    def selected_get(store, category, name):
        if combined and category == "COACCH":
            assert name.startswith("combined_"), f"Unneeded source requested: {name}"
        return get(store, category, name)

    monkeypatch.setattr(RegionalParamStore, "get", selected_get)
    model = MIMOSA(config(combined, adaptation, 0.84), prerun=False)
    check_selected_parameters(
        model.concrete_model, model.model_context.inputs.regional_store,
        combined, adaptation, 0.84
    )
