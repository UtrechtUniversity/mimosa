"""Utilities for constructing the model's calendar-year time grid."""

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class TimeGrid:
    """Calendar years and interval lengths for integer model timesteps."""

    years: Tuple[float, ...]
    period_lengths: Tuple[float, ...]

    @property
    def end(self) -> float:
        return self.years[-1]


def create_time_grid(time_params: dict) -> TimeGrid:
    """Build a time grid from start/end years and timestep change points.

    ``dt`` sets the initial timestep length. ``periods`` optionally maps a
    calendar year to the new timestep length used after that year. For example,
    ``dt=5`` and ``periods={2050: 10}`` produces five-year timesteps through
    2050 and ten-year timesteps thereafter. Every change year and the final
    year must lie exactly on the resulting grid.
    """

    start = float(time_params["start"])
    end = float(time_params["end"])
    initial_length = float(time_params["dt"])
    periods = time_params["periods"]
    if end <= start:
        raise ValueError("time.end must be greater than time.start")
    if initial_length <= 0:
        raise ValueError("time.dt must be positive")

    years = [start]
    current = start
    period_length = initial_length

    def append_until(target, length, target_name):
        nonlocal current
        number_of_steps = (target - current) / length
        rounded_steps = round(number_of_steps)
        if not np.isclose(number_of_steps, rounded_steps):
            raise ValueError(
                f"{target_name} {target:g} is not reachable from {current:g} "
                f"with {length:g}-year timesteps"
            )

        years.extend(
            current + length * step for step in range(1, rounded_steps + 1)
        )
        current = target

    for change_year, length in sorted(periods.items()):
        change_year = float(change_year)
        length = float(length)
        if length <= 0:
            raise ValueError("time.periods timestep lengths must be positive")

        # A change at or before the model start determines the active initial
        # length. This keeps the same period schedule usable with a later start.
        if change_year <= start:
            period_length = length
            continue
        # Changes beyond the configured horizon do not affect this run.
        if change_year >= end:
            break

        append_until(change_year, period_length, "Timestep change year")
        period_length = length

    append_until(end, period_length, "time.end")

    period_lengths = [0.0]
    period_lengths.extend(
        year - previous_year for previous_year, year in zip(years, years[1:])
    )
    return TimeGrid(tuple(years), tuple(period_lengths))
