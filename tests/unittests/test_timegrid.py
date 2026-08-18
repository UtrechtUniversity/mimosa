import pytest

from mimosa.common.timegrid import create_time_grid


def time_params(end=2100, dt=5, periods=None, start=2025):
    return {
        "start": start,
        "end": end,
        "dt": dt,
        "periods": {} if periods is None else periods,
    }


def test_create_time_grid_with_one_timestep_change():
    grid = create_time_grid(time_params(periods={2050: 10}))

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


def test_create_time_grid_without_changes_is_uniform():
    grid = create_time_grid(time_params(end=2050))

    assert grid.years == (2025.0, 2030.0, 2035.0, 2040.0, 2045.0, 2050.0)
    assert grid.period_lengths == (0.0,) + (5.0,) * 5


def test_create_time_grid_supports_multiple_changes():
    grid = create_time_grid(
        time_params(end=2290, periods={2050: 10, 2150: 20})
    )

    assert grid.years[:6] == (2025.0, 2030.0, 2035.0, 2040.0, 2045.0, 2050.0)
    assert grid.years[6:16] == tuple(range(2060, 2160, 10))
    assert grid.years[16:] == tuple(range(2170, 2300, 20))
    assert grid.period_lengths == (0.0,) + (5.0,) * 5 + (10.0,) * 10 + (
        20.0,
    ) * 7


def test_changes_after_end_are_ignored():
    grid = create_time_grid(time_params(end=2040, periods={2050: 10}))

    assert grid.years == (2025.0, 2030.0, 2035.0, 2040.0)


def test_change_at_model_start_sets_initial_length():
    grid = create_time_grid(
        time_params(start=2050, end=2080, periods={2050: 10})
    )

    assert grid.years == (2050.0, 2060.0, 2070.0, 2080.0)


@pytest.mark.parametrize(
    ("params", "message"),
    [
        (time_params(start=2025, end=2025), "greater than time.start"),
        (time_params(dt=0), "time.dt must be positive"),
        (
            time_params(periods={2052: 10}),
            "Timestep change year 2052 is not reachable",
        ),
        (
            time_params(end=2300, periods={2050: 10, 2150: 20}),
            "time.end 2300 is not reachable",
        ),
        (time_params(periods={2050: 0}), "lengths must be positive"),
    ],
)
def test_create_time_grid_rejects_invalid_configuration(params, message):
    with pytest.raises(ValueError, match=message):
        create_time_grid(params)
