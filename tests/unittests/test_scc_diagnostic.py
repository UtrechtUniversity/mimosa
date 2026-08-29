from functools import partial

import numpy as np
import pytest

from diagnostics.scc import (
    calculate_discounted_cost_scc,
    global_climate_costs,
    global_sector_costs,
    ramsey_discount_factors,
)
from mimosa.common import quant


class DamageValues(dict):
    unit = quant.unit("currency_unit", pyomo=False)


class DamageSimulation:
    t = (0, 1, 2)
    regions = ("A", "B")
    damage_costs_abs = {}
    adaptation_costs_abs = {}

    @staticmethod
    def year(t):
        return (2025, 2030, 2040)[t]


def damage_simulation(damage_per_region, adaptation_per_region=None):
    simulation = DamageSimulation()
    simulation.damage_costs_abs = DamageValues(
        {
            (t, region): damage_per_region[t]
            for t in simulation.t
            for region in simulation.regions
        }
    )
    adaptation_per_region = adaptation_per_region or [0.0, 0.0, 0.0]
    simulation.adaptation_costs_abs = DamageValues(
        {
            (t, region): adaptation_per_region[t]
            for t in simulation.t
            for region in simulation.regions
        }
    )
    return simulation


def test_discounted_cost_scc_uses_central_difference_and_variable_grid():
    negative = damage_simulation([0.0, 0.0, 0.0])
    positive = damage_simulation([0.0, 1.0, 1.0])

    scc = calculate_discounted_cost_scc(
        negative,
        positive,
        global_climate_costs,
        pulse_year=2030,
        pulse_size=1.0,
        discount_rate=0.03,
    )

    # Two regions give a central-difference marginal damage of 1 trillion
    # USD/year/GtCO2. Integrate this from 2030 to 2040 and convert to USD/tCO2.
    integrated_damages = 10 * (1 + np.exp(-0.03 * 10)) / 2
    expected = (
        integrated_damages
        * quant.unit("currency_unit", pyomo=False)
        * quant.unit("yr", pyomo=False)
        / quant.unit("emissions_unit", pyomo=False)
    ).to("USD2010/tCO2").magnitude
    assert scc == pytest.approx(expected)


def test_discounted_cost_scc_can_include_adaptation_costs():
    negative = damage_simulation([0.0, 0.0, 0.0], [0.0, 0.0, 0.0])
    positive = damage_simulation([0.0, 0.0, 0.0], [0.0, 1.0, 1.0])

    without_adaptation = calculate_discounted_cost_scc(
        negative,
        positive,
        global_climate_costs,
    )
    with_adaptation = calculate_discounted_cost_scc(
        negative,
        positive,
        partial(global_climate_costs, include_adaptation_costs=True),
    )

    assert without_adaptation == 0.0
    assert with_adaptation > 0.0


def test_global_sector_costs_include_sector_adaptation_expenditure():
    simulation = DamageSimulation()
    simulation.GDP_gross = {(0, "A"): 2.0, (0, "B"): 3.0}
    simulation.sector_damage_costs = {(0, "A"): 0.1, (0, "B"): 0.2}
    simulation.sector_adaptation_costs_abs = {(0, "A"): 1.0, (0, "B"): 2.0}

    costs = global_sector_costs(
        simulation,
        0,
        "sector_damage_costs",
        "sector_adaptation_costs_abs",
    )

    assert costs == pytest.approx(0.1 * 2.0 + 0.2 * 3.0 + 1.0 + 2.0)


def test_ramsey_discount_factors_use_global_per_capita_consumption():
    simulation = DamageSimulation()
    simulation.consumption = {
        (t, region): value
        for t, value in enumerate((1.0, 2.0, 4.0))
        for region in simulation.regions
    }
    simulation.population = {
        (t, region): 1.0 for t in simulation.t for region in simulation.regions
    }

    factors = ramsey_discount_factors(
        simulation,
        prtp=0.01,
        elasmu=2.0,
        pulse_year=2030,
    )

    expected = np.exp(-0.01 * (np.asarray([2025, 2030, 2040]) - 2030)) * np.asarray(
        [0.5, 1.0, 2.0]
    ) ** -2.0
    np.testing.assert_allclose(factors, expected)
