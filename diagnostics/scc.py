"""Calculate the SCC from discounted additional global damages.

Run from the repository root with:

    python diagnostics/scc.py
"""

from copy import deepcopy
from functools import partial
from pathlib import Path
import sys

import numpy as np

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from mimosa import MIMOSA, load_params  # noqa: E402
from mimosa.common import quant, trapezoid  # noqa: E402

PULSE_YEAR = 2030
PULSE_SIZE = 1.0  # GtCO2
DISCOUNT_RATE = 0.03

SECTORS = {
    "COACCH": {
        "non-SLR": ("non_slr_damage_costs", None),
        "SLR": ("slr_damage_costs", None),
    },
    "ACCREU": {
        "labour productivity": (
            "labourprod_damage_costs_net",
            "labourprod_adaptation_costs_abs",
        ),
        "riverine flooding": (
            "riverine_damage_costs",
            "riverine_adaptation_costs_abs",
        ),
        "SLR": ("slr_damage_costs", "slr_adaptation_costs_abs"),
    },
}


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


def global_climate_costs(simulation, t, include_adaptation_costs=False):
    """Return global damages, optionally including adaptation expenditure."""

    costs = sum(simulation.damage_costs_abs[t, region] for region in simulation.regions)
    if include_adaptation_costs:
        costs += sum(
            simulation.adaptation_costs_abs[t, region] for region in simulation.regions
        )
    return costs


def global_sector_costs(
    simulation,
    t,
    damage_variable,
    adaptation_cost_variable=None,
):
    """Return one sector's global damages and adaptation expenditure."""

    damage_costs = getattr(simulation, damage_variable)
    costs = sum(
        damage_costs[t, region] * simulation.GDP_gross[t, region]
        for region in simulation.regions
    )
    if adaptation_cost_variable and hasattr(simulation, adaptation_cost_variable):
        adaptation_costs = getattr(simulation, adaptation_cost_variable)
        costs += sum(adaptation_costs[t, region] for region in simulation.regions)
    return costs


def calculate_discounted_cost_scc(
    negative_pulse,
    positive_pulse,
    global_cost_function,
    pulse_year=PULSE_YEAR,
    pulse_size=PULSE_SIZE,
    discount_rate=DISCOUNT_RATE,
):
    """Discount a central-difference stream of global costs."""

    years = np.asarray([positive_pulse.year(t) for t in positive_pulse.t], dtype=float)
    marginal_costs = np.asarray(
        [
            (
                global_cost_function(positive_pulse, t)
                - global_cost_function(negative_pulse, t)
            )
            / (2 * pulse_size)
            for t in positive_pulse.t
        ]
    )

    included = years >= pulse_year
    included_years = years[included]
    discount_factors = np.exp(-discount_rate * (included_years - pulse_year))
    discounted_costs = trapezoid(
        marginal_costs[included] * discount_factors,
        included_years,
    )

    scc_units = (
        positive_pulse.damage_costs_abs.unit
        * quant.unit("yr", pyomo=False)
        / quant.unit("emissions_unit", pyomo=False)
    )
    return (discounted_costs * scc_units).to("USD2010/tCO2").magnitude


def calculate_scc_breakdown(
    params,
    damage_module,
    controls=None,
    include_adaptation_costs=False,
    pulse_size=PULSE_SIZE,
):
    """Calculate the total and sectoral SCCs for supplied policy controls."""

    negative = simulate_with_pulse(params, -pulse_size, controls)
    positive = simulate_with_pulse(params, pulse_size, controls)

    sccs = {
        "total": calculate_discounted_cost_scc(
            negative,
            positive,
            partial(
                global_climate_costs,
                include_adaptation_costs=include_adaptation_costs,
            ),
            pulse_size=pulse_size,
        )
    }
    for sector, (damage_variable, adaptation_cost_variable) in SECTORS[
        damage_module
    ].items():
        if not include_adaptation_costs:
            adaptation_cost_variable = None
        sccs[sector] = calculate_discounted_cost_scc(
            negative,
            positive,
            partial(
                global_sector_costs,
                damage_variable=damage_variable,
                adaptation_cost_variable=adaptation_cost_variable,
            ),
            pulse_size=pulse_size,
        )
    return sccs


def base_params(damage_module):
    """Load parameters shared by all SCC scenarios for a damage module."""

    params = load_params()
    params["emissions"]["baseline carbon intensity"] = False
    params["economics"]["damages"]["ignore damages"] = False
    params["model structure"]["damage module"] = damage_module
    return params


def no_adaptation(params):
    """Return a copy of ACCREU parameters with adaptation disabled."""

    params = deepcopy(params)
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "noadaptation"
    options["ACCREU_adaptation_determination"] = "solver_control"
    options["ACCREU_CBA_strategy"] = "joint"
    return params


def analytical_adaptation(params):
    """Return a copy using ACCREU's analytical optimal adaptation."""

    params = deepcopy(params)
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "separate"
    options["ACCREU_adaptation_determination"] = "analytical_optimum"
    options["ACCREU_CBA_strategy"] = "joint"
    return params


def calculate_coacch_sccs(pulse_size=PULSE_SIZE):
    """Calculate COACCH baseline and fixed-optimal-path SCC values."""

    params = base_params("COACCH")

    sccs = {
        "baseline": calculate_scc_breakdown(params, "COACCH", pulse_size=pulse_size)
    }

    model = MIMOSA(deepcopy(params))
    model.solve(verbose=False)
    controls = extract_optimal_controls(model)
    sccs["optimal"] = calculate_scc_breakdown(
        params, "COACCH", controls, pulse_size=pulse_size
    )
    return sccs


def calculate_accreu_sccs(pulse_size=PULSE_SIZE):
    """Calculate the four standard ACCREU policy-scenario SCC values."""

    params = base_params("ACCREU")
    params_without_adaptation = no_adaptation(params)

    # baseline: no mitigation and no adaptation
    sccs = {
        "baseline": calculate_scc_breakdown(
            params_without_adaptation,
            "ACCREU",
            pulse_size=pulse_size,
        )
    }

    # mit: optimal mitigation with adaptation disabled
    mitigation_model = MIMOSA(deepcopy(params_without_adaptation))
    mitigation_model.solve(verbose=False)
    mitigation_controls = extract_optimal_controls(mitigation_model)
    sccs["mit"] = calculate_scc_breakdown(
        params_without_adaptation,
        "ACCREU",
        mitigation_controls,
        pulse_size=pulse_size,
    )

    # ada: no mitigation and analytical adaptation, recalculated for each pulse
    adaptation_params = analytical_adaptation(params)
    sccs["ada"] = calculate_scc_breakdown(
        adaptation_params,
        "ACCREU",
        include_adaptation_costs=True,
        pulse_size=pulse_size,
    )
    return sccs


def print_sccs(damage_module, sccs):
    """Print labelled SCC results for one damage module."""

    for scenario, breakdown in sccs.items():
        print(
            f"{damage_module} {scenario} SCC in {PULSE_YEAR}: "
            f"{breakdown['total']:.2f} USD2010/tCO2"
        )
        for sector, scc in breakdown.items():
            if sector != "total":
                print(f"  {sector}: {scc:.2f} USD2010/tCO2")


if __name__ == "__main__":
    print_sccs("COACCH", calculate_coacch_sccs())
    print_sccs("ACCREU", calculate_accreu_sccs())
