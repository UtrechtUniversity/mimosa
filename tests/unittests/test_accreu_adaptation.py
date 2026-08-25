import pytest

from mimosa.components.damages.accreu.utils import (
    get_adaptation_calibration,
    validate_adaptation_calibration,
)


@pytest.mark.parametrize("sector", ["labourprod", "riverine", "slr"])
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
        ("literature", "labourprod", 1.0, 1.0),
        ("literature", "riverine", 0.618, 1.0),
        ("literature", "slr", 0.659, 0.25),
        ("literature_high", "labourprod", 1.977, 2.0),
        ("literature_high", "riverine", 0.721, 2.0),
        ("literature_high", "slr", 0.933, 0.5),
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
def test_literature_calibration_requires_separate_adaptation(calibration):
    with pytest.raises(ValueError, match="requires.*separate"):
        validate_adaptation_calibration(calibration, "combined")

    validate_adaptation_calibration(calibration, "separate")
