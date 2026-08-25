from types import SimpleNamespace

import pytest

from mimosa.components.damages.accreu.utils import (
    effective_adaptation_curve,
    get_adaptation_calibration,
    get_adaptation_options,
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
    assert effective_cost_param == pytest.approx(4.0 * 0.5 / 2.0)


def test_adaptation_options_are_read_once_and_include_sector_calibrations():
    values = {
        "ACCREU adaptation": "combined",
        "ACCREU_adaptation_calibration": "accreu",
        "ACCREU_adaptation_impose_optimal": True,
    }
    calls = []

    class Context:
        def option(self, component, name, default=None):
            calls.append((component, name))
            return values.get(name, default)

    options = get_adaptation_options(Context())

    assert options.adaptation_type == "combined"
    assert options.impose_optimal is True
    assert set(options.calibrations) == {
        "labourprod",
        "riverine",
        "slr",
        "combined",
    }
    assert calls == [
        ("damage", "ACCREU adaptation"),
        ("damage", "ACCREU_adaptation_calibration"),
        ("damage", "ACCREU_adaptation_impose_optimal"),
    ]


@pytest.mark.parametrize("sector", ["labourprod", "riverine", "slr", "combined"])
def test_accreu_calibration_preserves_source_coefficients(sector):
    calibration = get_adaptation_calibration("accreu", sector)

    assert calibration.max_effectiveness_scale == 1
    assert calibration.cost_param_scale == 1


@pytest.mark.parametrize(
    ("calibration", "sector", "max_scale", "cost_scale"),
    [
        ("literature_low", "labourprod", 0.741, 0.167),
        ("literature_low", "riverine", 0.412, 0.167),
        ("literature_low", "slr", 0.439, 0.125),
        ("literature_low", "combined", 0.645, 0.167),
        ("literature", "labourprod", 1.0, 1.0),
        ("literature", "riverine", 0.618, 1.0),
        ("literature", "slr", 0.659, 0.25),
        ("literature", "combined", 0.889, 1.0),
        ("literature_high", "labourprod", 1.977, 2.0),
        ("literature_high", "riverine", 0.721, 2.0),
        ("literature_high", "slr", 0.933, 0.5),
        ("literature_high", "combined", 1.25, 4.0),
    ],
)
def test_literature_calibration_uses_sector_specific_factors(
    calibration, sector, max_scale, cost_scale
):
    factors = get_adaptation_calibration(calibration, sector)

    assert factors.max_effectiveness_scale == pytest.approx(max_scale)
    assert factors.cost_param_scale == pytest.approx(cost_scale)


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
