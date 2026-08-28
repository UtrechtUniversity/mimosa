import numpy as np
import pytest

from diagnostics.scc import calculate_discounted_damage_scc


class DamageSimulation:
    t = (0, 1, 2)
    regions = ("A", "B")
    damage_costs_abs = {}

    @staticmethod
    def year(t):
        return (2025, 2030, 2040)[t]


def damage_simulation(damage_per_region):
    simulation = DamageSimulation()
    simulation.damage_costs_abs = {
        (t, region): damage_per_region[t]
        for t in simulation.t
        for region in simulation.regions
    }
    return simulation


def test_discounted_damage_scc_uses_central_difference_and_variable_grid():
    negative = damage_simulation([0.0, 0.0, 0.0])
    positive = damage_simulation([0.0, 1.0, 1.0])

    scc = calculate_discounted_damage_scc(
        negative,
        positive,
        pulse_year=2030,
        pulse_size=1.0,
        discount_rate=0.03,
    )

    # Two regions give a central-difference marginal damage of 1 trillion
    # USD/year/GtCO2. Integrate this from 2030 to 2040 and convert to USD/tCO2.
    expected = 1000 * 10 * (1 + np.exp(-0.03 * 10)) / 2
    assert scc == pytest.approx(expected)
