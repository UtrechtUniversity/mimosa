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
    """Build a time grid from a start year and endpoint-to-length periods.

    ``periods`` maps each period's inclusive end year to its timestep length.
    For example, ``{2050: 5, 2150: 10}`` produces five-year timesteps through
    2050 and ten-year timesteps thereafter. Each period must fit an integer
    number of timesteps exactly.
    """

    start = float(time_params["start"])
    periods = time_params["periods"]
    if not periods:
        raise ValueError("time.periods must define at least one period")

    years = [start]
    current = start

    for end, length in sorted(periods.items()):
        end = float(end)
        length = float(length)
        if end <= current:
            raise ValueError(
                "time.periods endpoints must be strictly increasing and greater "
                f"than the preceding year ({current:g})"
            )
        if length <= 0:
            raise ValueError("time.periods timestep lengths must be positive")

        number_of_steps = (end - current) / length
        rounded_steps = round(number_of_steps)
        if not np.isclose(number_of_steps, rounded_steps):
            raise ValueError(
                f"Period {current:g}-{end:g} is not divisible by its "
                f"{length:g}-year timestep"
            )

        years.extend(current + length * step for step in range(1, rounded_steps + 1))
        current = end

    period_lengths = [0.0]
    period_lengths.extend(
        year - previous_year for previous_year, year in zip(years, years[1:])
    )
    return TimeGrid(tuple(years), tuple(period_lengths))
