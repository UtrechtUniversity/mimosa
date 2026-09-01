from types import SimpleNamespace

import pytest
from pyomo.environ import Any, ConcreteModel, Param, Set, Var, value

from mimosa.components.damages.accreu.utils import (
    effective_adaptation_curve,
    get_adaptation_calibration,
    get_adaptation_options,
    get_delayed_adaptation_constraint,
    optimal_adaptation_costs_fct,
    validate_adaptation_calibration,
)


def test_effective_adaptation_curve_applies_all_scale_factors():
    model = SimpleNamespace(
        adaptation_effectiveness_scale_factor=0.5,
        dollar_2017_MER_to_2010_PPP={"region": 2.0},
    )
    calibration = get_adaptation_calibration("literature_high", "slr")

    effective_max, effective_cost_param = effective_adaptation_curve(
        model,
        "region",
        source_max_effectiveness=0.8,
        source_cost_param=4.0,
        calibration=calibration,
    )

    assert effective_max == pytest.approx(0.8 * 0.933 * 0.5)
    assert effective_cost_param == pytest.approx(4.0 / 2.0 / 2.0)


def test_adaptation_options_are_read_once_and_include_sector_calibrations():
    values = {
        "ACCREU_adaptation": "combined",
        "ACCREU_adaptation_calibration": "accreu",
        "ACCREU_adaptation_determination": "analytical_optimum",
    }
    calls = []

    class Context:
        def option(self, component, name, default=None):
            calls.append((component, name))
            return values.get(name, default)

    options = get_adaptation_options(Context())

    assert options.adaptation_type == "combined"
    assert options.uses_analytical_adaptation is True
    assert options.determination == "analytical_optimum"
    assert set(options.calibrations) == {
        "labourprod",
        "riverine",
        "slr",
        "combined",
    }
    assert calls == [
        ("damage", "ACCREU_adaptation"),
        ("damage", "ACCREU_adaptation_calibration"),
        ("damage", "ACCREU_adaptation_determination"),
    ]


@pytest.mark.parametrize("sector", ["labourprod", "riverine", "slr", "combined"])
def test_accreu_calibration_preserves_source_coefficients(sector):
    calibration = get_adaptation_calibration("accreu", sector)

    assert calibration.max_effectiveness_scale == 1
    assert calibration.cost_multiplier == 1


@pytest.mark.parametrize(
    ("calibration", "sector", "max_scale", "cost_multiplier"),
    [
        ("literature_low", "labourprod", 0.741, 6.0),
        ("literature_low", "riverine", 0.412, 6.0),
        ("literature_low", "slr", 0.439, 8.0),
        ("literature_low", "combined", 0.645, 6.0),
        ("literature", "labourprod", 1.0, 1.0),
        ("literature", "riverine", 0.618, 1.0),
        ("literature", "slr", 0.659, 4.0),
        ("literature", "combined", 0.889, 1.0),
        ("literature_high", "labourprod", 1.977, 0.5),
        ("literature_high", "riverine", 0.721, 0.5),
        ("literature_high", "slr", 0.933, 2.0),
        ("literature_high", "combined", 1.25, 0.25),
    ],
)
def test_literature_calibration_uses_sector_specific_factors(
    calibration, sector, max_scale, cost_multiplier
):
    factors = get_adaptation_calibration(calibration, sector)

    assert factors.max_effectiveness_scale == pytest.approx(max_scale)
    assert factors.cost_multiplier == pytest.approx(cost_multiplier)


@pytest.mark.parametrize(
    ("calibration", "sector", "message"),
    [
        ("unknown", "slr", "Unknown ACCREU adaptation calibration"),
        ("literature", "unknown", "Unknown ACCREU adaptation sector"),
    ],
)
def test_adaptation_calibration_rejects_unknown_values(calibration, sector, message):
    with pytest.raises(ValueError, match=message):
        get_adaptation_calibration(calibration, sector)


@pytest.mark.parametrize(
    "calibration", ["literature_low", "literature", "literature_high"]
)
def test_literature_calibration_supports_combined_adaptation(calibration):
    validate_adaptation_calibration(calibration)
    get_adaptation_calibration(calibration, "combined")


def _delayed_adaptation_model(delay_year):
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1, 2, 3], ordered=True)
    model.regions = Set(initialize=["A", "B"], ordered=True)
    model.year = lambda t: 2025 + 5 * t
    model.delay_adaptation_year = Param(initialize=delay_year, within=Any)
    model.sector_adaptation_costs = Var(
        model.t, model.regions, initialize=0.00005
    )
    model.delayed_adaptation = get_delayed_adaptation_constraint(
        "sector_adaptation_costs"
    ).to_pyomo_constraint(model)
    return model


def test_delayed_adaptation_constraint_applies_through_delay_year():
    model = _delayed_adaptation_model(2035)

    assert set(model.delayed_adaptation) == {
        (0, "A"),
        (0, "B"),
        (1, "A"),
        (1, "B"),
        (2, "A"),
        (2, "B"),
    }
    for constraint in model.delayed_adaptation.values():
        assert constraint.lower is None
        assert value(constraint.upper) == pytest.approx(0.00005)


def test_delayed_adaptation_constraint_is_skipped_when_disabled():
    model = _delayed_adaptation_model(False)

    assert len(model.delayed_adaptation) == 0


@pytest.mark.parametrize(
    ("year", "is_delayed"),
    [(2030, True), (2035, True), (2040, False)],
)
def test_analytical_adaptation_uses_same_delay_year_boundary(year, is_delayed):
    model = SimpleNamespace(delay_adaptation_year=2035, year=lambda _t: year)

    result = optimal_adaptation_costs_fct(
        model,
        0,
        gross_damages_abs=10,
        a=0.5,
        b=2,
    )

    if is_delayed:
        assert result == 0
    else:
        assert result > 0
