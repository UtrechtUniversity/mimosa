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


def test_literature_calibration_uses_sector_specific_factors():
    labour = get_adaptation_calibration("literature", "labourprod")
    riverine = get_adaptation_calibration("literature", "riverine")
    slr = get_adaptation_calibration("literature", "slr")

    assert labour.max_effectiveness_scale == 1
    assert labour.cost_param_scale == 1
    assert riverine.max_effectiveness_scale == pytest.approx(0.618)
    assert riverine.cost_param_scale == 1
    assert slr.max_effectiveness_scale == pytest.approx(0.659)
    assert slr.cost_param_scale == pytest.approx(0.25)


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


def test_literature_calibration_requires_separate_adaptation():
    with pytest.raises(ValueError, match="requires.*separate"):
        validate_adaptation_calibration("literature", "combined")

    validate_adaptation_calibration("literature", "separate")
