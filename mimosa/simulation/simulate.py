import time
import numpy as np
from scipy.optimize import minimize

from mimosa.common import RegionalEquation, GlobalEquation, Var
from .objects import SimulationObjectModel


def simulate(sim_m, equations_sorted, show_time=False):

    if show_time:
        t1 = time.time()

    for t in sim_m.t:
        for equation in equations_sorted:
            # Check if it is a regional or global equation
            if isinstance(equation, RegionalEquation):  # Regional:
                try:
                    r = slice(None)
                    value = equation(sim_m, t, r)
                    getattr(sim_m, equation.lhs)[t, r] = value
                except (TypeError, NotImplementedError):
                    # print(var_name, t)
                    for r in sim_m.regions:
                        value = equation(sim_m, t, r)
                        getattr(sim_m, equation.lhs)[t, r] = value
            elif isinstance(equation, GlobalEquation):  # Global:
                value = equation(sim_m, t)
                getattr(sim_m, equation.lhs)[t] = value
            else:
                raise ValueError(
                    f"Equation {equation.name} is neither Regional nor Global."
                )
    if show_time:
        t2 = time.time()
        print(f"Time taken to evaluate all expressions: {t2 - t1:.3f} seconds")


def find_linear_abatement(x, sim_m, equations_sorted, return_npv_only=True):

    n_t = len(sim_m.t)
    n_r = len(sim_m.regions)

    # Set the relative abatement for all regions and time periods
    sim_m.relative_abatement.values = x.reshape((n_t, 1)).repeat(n_r, axis=1)

    # Run the simulation
    simulate(sim_m, equations_sorted)

    # Return final NPV
    if return_npv_only:
        return -sim_m.NPV[n_t - 1]
    return sim_m


def initial_guess(sim_m):
    n_t = len(sim_m.t)
    # n_r = len(start_sim_m.regions)
    n_r = 1

    bounds = [[(0, xmax)] * n_r for xmax in 0.75 + np.linspace(0, 1.5, n_t)]
    bounds = sum(bounds, [])

    p = 0.7
    x0 = np.array([p * b[0] + (1 - p) * b[1] for b in bounds])

    return x0, bounds


def find_prerun_bestguess(m, equations_sorted):
    # Create the simulation model that will be used in the initial guessing
    sim_m = SimulationObjectModel(m)

    # Get the initial guess for the optimisation
    x0, bounds = initial_guess(sim_m)

    # Perform first step of scipy optimisation to find a good initial guess:
    result = minimize(
        lambda x: find_linear_abatement(x, sim_m, equations_sorted),
        x0=x0,
        bounds=bounds,
        options={"maxiter": 1},
    )

    # Evaluate the simulation model with the result of the optimisation
    sim_m = find_linear_abatement(
        result.x,
        sim_m,
        equations_sorted,
        return_npv_only=False,
    )
    sim_m.regions = sim_m.regions_names
    sim_m.t = sim_m.t_names

    return sim_m


def run_nopolicy_baseline(m, equations_sorted):
    """
    Run the simulation model without any policy, i.e. with the baseline emissions.
    This is used to find a good initial guess for the optimisation.
    """
    # Create the simulation model
    sim_m = SimulationObjectModel(m)

    x0, _ = initial_guess(sim_m)

    sim_m = find_linear_abatement(
        x0 * 0.0,  # No abatement, i.e. baseline emissions
        sim_m,
        equations_sorted,
        return_npv_only=False,
    )
    sim_m.regions = sim_m.regions_names
    sim_m.t = sim_m.t_names

    return sim_m


def initialize_pyomo_model(pyomo_model, simulation_model):
    for var in pyomo_model.component_objects(Var):
        name = var.name
        if not name.startswith("_"):
            if var.index_set().dimen > 0:
                for i in var.index_set().ordered_data():
                    getattr(pyomo_model, name)[i] = getattr(
                        simulation_model, name
                    ).get_indexed(i)
            else:
                print(var.name, var.value)
