"""Calculate the SCC from discounted additional global damages.

Run from the repository root with:

    python diagnostics/scc.py
"""

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from mimosa import MIMOSA, load_params  # noqa: E402
from mimosa.common import trapezoid  # noqa: E402

PULSE_YEAR = 2030
PULSE_SIZE = 1.0  # GtCO2
DISCOUNT_RATE = 0.03


def simulate_with_pulse(params, pulse, controls=None):
    """Run a simulation with one exogenous CO2 pulse in GtCO2."""

    pulse_params = deepcopy(params)
    pulse_params["emissions"]["pulse"]["year"] = PULSE_YEAR
    pulse_params["emissions"]["pulse"]["amount"] = f"{pulse} GtCO2"

    model = MIMOSA(pulse_params, prerun=False)
    return model.run_simulation(**(controls or {}))


def extract_optimal_controls(model):
    """Extract all simulation controls from an optimised model."""

    if not model.simulator.is_prepared:
        model.prepare_simulation()

    return {
        name: getattr(model.concrete_model, name).extract_values()
        for name in model.simulator.control_variables
    }


def global_damages(simulation, t):
    """Return global absolute damages in trillion USD2010 per year."""

    return sum(simulation.damage_costs_abs[t, region] for region in simulation.regions)


def calculate_discounted_damage_scc(
    negative_pulse,
    positive_pulse,
    pulse_year=PULSE_YEAR,
    pulse_size=PULSE_SIZE,
    discount_rate=DISCOUNT_RATE,
):
    """Calculate the pulse-year SCC in USD2010 per tCO2."""

    years = np.asarray([positive_pulse.year(t) for t in positive_pulse.t], dtype=float)
    marginal_damages = np.asarray(
        [
            (global_damages(positive_pulse, t) - global_damages(negative_pulse, t))
            / (2 * pulse_size)
            for t in positive_pulse.t
        ]
    )

    included = years >= pulse_year
    included_years = years[included]
    discount_factors = np.exp(-discount_rate * (included_years - pulse_year))
    discounted_damages = trapezoid(
        marginal_damages[included] * discount_factors,
        included_years,
    )

    # 1 trillion USD / GtCO2 = 1000 USD / tCO2.
    return discounted_damages * 1000


def calculate_scc_for_controls(params, controls=None):
    """Calculate the SCC along a fixed policy path."""

    negative = simulate_with_pulse(params, -PULSE_SIZE, controls)
    positive = simulate_with_pulse(params, PULSE_SIZE, controls)
    return calculate_discounted_damage_scc(negative, positive)


def calculate_sccs():
    """Calculate no-policy and fixed-optimal-path SCC values."""

    params = load_params()
    params["economics"]["damages"]["ignore damages"] = False

    baseline_scc = calculate_scc_for_controls(params)

    optimal_model = MIMOSA(deepcopy(params))
    optimal_model.solve(verbose=False)
    optimal_controls = extract_optimal_controls(optimal_model)
    optimal_scc = calculate_scc_for_controls(params, optimal_controls)

    return baseline_scc, optimal_scc


if __name__ == "__main__":
    baseline_scc, optimal_scc = calculate_sccs()
    print(f"Baseline SCC in {PULSE_YEAR}: {baseline_scc:.2f} USD2010/tCO2")
    print(f"Optimal-path SCC in {PULSE_YEAR}: {optimal_scc:.2f} USD2010/tCO2")
