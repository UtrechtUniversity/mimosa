import pytest

from mimosa.common.timegrid import create_time_grid


def test_create_time_grid_with_varying_period_lengths():
    grid = create_time_grid({"start": 2025, "periods": {2050: 5, 2100: 10}})

    assert grid.years == (
        2025.0,
        2030.0,
        2035.0,
        2040.0,
        2045.0,
        2050.0,
        2060.0,
        2070.0,
        2080.0,
        2090.0,
        2100.0,
    )
    assert grid.period_lengths == (0.0,) + (5.0,) * 5 + (10.0,) * 5


@pytest.mark.parametrize(
    ("periods", "message"),
    [
        ({}, "at least one period"),
        ({2020: 5}, "strictly increasing"),
        ({2052: 5}, "not divisible"),
    ],
)
def test_create_time_grid_rejects_invalid_periods(periods, message):
    with pytest.raises(ValueError, match=message):
        create_time_grid({"start": 2025, "periods": periods})
