import itertools
from collections import Counter

import numpy as np
import pandas as pd
import networkx as nx
from scipy.optimize import minimize

from mimosa.common import RegionalEquation, GlobalEquation, Var, ConcreteModel
from .objects import SimulationObjectModel, SimVar
from .helpers import calc_dependencies, sort_equations, plot_dependency_graph


class SimulationNotPreparedError(RuntimeError):
    """Raised when simulation is requested before dependencies are prepared."""


class Simulator:
    """
    Simulator class for MIMOSA.

    Before running any simulation, the equations must be prepared using the
    `prepare_simulation` method. This method checks for circular dependencies
    between equations and sorts them based on their dependencies.

    After preparation, the `run` method can be used to perform the simulation.
    It allows setting "free" variables, such as relative abatement, and runs the
    simulation based on the sorted equations.

    """

    concrete_model: ConcreteModel
    equations: list
    equations_sorted: list
    equations_graph: nx.DiGraph
    control_variables: list

    def __init__(self):
        self.reset()

    def reset(self):
        self.concrete_model = None
        self.equations = []
        self.equations_sorted = []
        self.equations_graph = None
        self.control_variables = []
        self._is_prepared = False

    @property
    def is_prepared(self):
        """Whether the simulator has a complete, valid execution plan."""
        return self._is_prepared

    def prepare_simulation(self, equations, concrete_model):
        """
        Prepares the model for simulation mode: it gathers all the equations,
        checks for circular dependencies, and sorts the equations based on their
        dependencies.
        """

        # Clear derived state first so failed re-preparation cannot leave an old
        # execution plan that appears usable with a new model or equation set.
        self.reset()

        self.equations = list(equations)
        self.concrete_model = concrete_model

        equation_name_counts = Counter(eq.name for eq in self.equations)
        duplicate_equation_names = sorted(
            name for name, count in equation_name_counts.items() if count > 1
        )
        if duplicate_equation_names:
            raise ValueError(
                "Duplicate equation definitions for: "
                + ", ".join(duplicate_equation_names)
            )

        # Check the dependencies between variables and equations to test
        # if there are circular dependencies. If there are, it is not possible
        # to run in simulation mode.
        equations_dict = {eq.name: eq for eq in self.equations}
        calc_dependencies(equations_dict, concrete_model)
        # Perform topological sort of equations based on dependencies
        self.equations_sorted, self.equations_graph, self.control_variables = (
            sort_equations(equations_dict, return_graph=True)
        )
        self._is_prepared = True

    def run(self, simulation_model=None, **control_variables_kwargs):
        """
        Runs MIMOSA as simulation.

        It first sets the "free" variables (relative_abatement), then runs the simulation

        Args:
        simulation_model (SimulationObjectModel): The simulation model to run.
            If None, a new SimulationObjectModel will be created.
        control_variables_kwargs: set of keyword arguments to optionally set free variables to a value. Can be:
            * None (equivalent to 0)
            * A float value: every region and time step will get this value
            * A numpy array of shape (n_timesteps, n_regions): each region and time step will get the corresponding value
              (or shape (n_timesteps,) for global variables)
        """

        self._require_prepared()

        if simulation_model is None:
            # Create a SimulationObjectModel object that will be used to run the simulation
            simulation_model = SimulationObjectModel(self.concrete_model)

        # Check if there are no variables provided in kwargs that are not in the free variables:
        for var in control_variables_kwargs:
            if var not in self.control_variables:
                raise ValueError(
                    f"Variable '{var}' is not a control variable. "
                    f"Available control variables: {self.control_variables}"
                )

        for var in self.control_variables:
            # Check if the variable is provided in the kwargs, otherwise set to None
            value = control_variables_kwargs.get(var, None)

            if value is None:
                # If no value is provided, set it to zero
                value = 0

            # Get the variable in the simulation model to know its dimensions (e.g. if it is region/time dependent)
            sim_var = getattr(simulation_model, var)

            # First check if it is given as a dictionary with (time, region) keys
            if isinstance(value, dict):
                # Convert the dictionary to a numpy array
                value = self._dict_to_array(value, sim_var)
            # If it is a single float value, convert it to a numpy array
            elif isinstance(value, (int, float)):
                value = np.full(sim_var.dims, value)

            # Check that the dimensions are correct
            expected_shape = tuple(sim_var.dims)
            assert value.shape == expected_shape, (
                f"{var} must be of shape {expected_shape}, " f"but is {value.shape}."
            )

            # Set the value for the control variable
            sim_var.values = value

        self._simulate(simulation_model)

        return simulation_model

    def find_prerun_bestguess(self):
        self._require_prepared()

        # Create the simulation model that will be used in the initial guessing
        sim_m = SimulationObjectModel(self.concrete_model)

        # Get the initial guess for the optimisation
        # For this prerun, we assume equal relative abatement in every region
        n_t = len(sim_m.t)
        n_r = len(sim_m.regions)

        bounds = [[(0, xmax)] for xmax in 0.75 + np.linspace(0, 1.5, n_t)]
        bounds = sum(bounds, [])

        p = 0.7
        x0 = np.array([p * b[0] + (1 - p) * b[1] for b in bounds])

        # Perform first step of scipy optimisation to find a good initial guess:
        def f(x, objective_only=True):
            # Set global relative abatement (x) to regional abatement in simulation
            relative_abatement = x.reshape((n_t, 1)).repeat(n_r, axis=1)
            # Do simulation
            self.run(sim_m, relative_abatement=relative_abatement)
            # Return the value to minimise (we try to maximise the final NPV)
            if objective_only:
                return -sim_m.NPV[n_t - 1]
            return sim_m

        result = minimize(f, x0=x0, bounds=bounds, options={"maxiter": 1})

        # Evaluate the simulation model with the result of the optimisation
        sim_m = f(result.x, objective_only=False)

        return sim_m

    def plot_dependency_graph(self):
        """
        Plots the dependency graph of the equations.
        """
        self._require_prepared()
        return plot_dependency_graph(self.equations_graph)

    ####################
    ##
    ## Static methods
    ##
    ####################

    @staticmethod
    def initialize_pyomo_model(pyomo_model, simulation_model):
        """
        Takes the values of a simulation model and sets them as initial values
        for the corresponding variables in a Pyomo model. This helps the
        optimisation to start from a good initial guess.
        """
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

    ####################
    ##
    ## Private functions
    ##
    ####################

    def _require_prepared(self):
        if not self._is_prepared:
            raise SimulationNotPreparedError(
                "Simulator is not prepared. Call prepare_simulation() first."
            )

    def _simulate(self, sim_m: SimulationObjectModel):
        """
        Given a SimulationModel object, evaluates all equations for every timestep
        """

        for t in sim_m.t:
            for equation in self.equations_sorted:
                # Check if we also need to loop over other dimensions (e.g. regions)
                indices = equation.indices
                if len(indices) == 1:
                    value = equation(sim_m, t)
                    getattr(sim_m, equation.lhs)[t] = value
                else:
                    # Loop over other indices
                    remaining_indices = indices[1:]
                    remaining_index_values = [
                        getattr(sim_m, index) for index in remaining_indices
                    ]

                    for remaining_idx in itertools.product(*remaining_index_values):
                        value = equation(sim_m, t, *remaining_idx)
                        idx_with_t = (t,) + tuple(remaining_idx)
                        getattr(sim_m, equation.lhs)[idx_with_t] = value

    def _dict_to_array(self, d: dict, sim_var: SimVar):
        """
        Converts a dictionary of values to a numpy array.
        The keys of the dictionary should be index items.
        For global variables, this is time (0, 1, ...).
        For regional variables, this is tuples of (time, region) ((0, 'CAN'), ..., (15, 'WEU'), ...).
        """
        indices = sim_var.indices_values

        shape = tuple(len(idx) for idx in indices)
        arr = np.empty(shape)

        for pos, key in zip(
            itertools.product(*(range(n) for n in shape)), itertools.product(*indices)
        ):
            # For 1D dictionaries, keys may be scalars rather than 1-tuples
            lookup_key = key[0] if len(key) == 1 else key
            arr[pos] = d[lookup_key]

        return arr
