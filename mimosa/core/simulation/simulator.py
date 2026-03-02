import itertools
import numpy as np
import pandas as pd
import networkx as nx
from scipy.optimize import minimize

from mimosa.common import RegionalEquation, GlobalEquation, Var, ConcreteModel
from .objects import SimulationObjectModel
from .helpers import calc_dependencies, sort_equations, plot_dependency_graph


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
        pass

    def prepare_simulation(self, equations, concrete_model):
        """
        Prepares the model for simulation mode: it gathers all the equations,
        checks for circular dependencies, and sorts the equations based on their
        dependencies.
        """

        self.equations = equations
        self.concrete_model = concrete_model

        # Check the dependencies between variables and equations to test
        # if there are circular dependencies. If there are, it is not possible
        # to run in simulation mode.
        equations_dict = {eq.name: eq for eq in equations}
        calc_dependencies(equations_dict, concrete_model)
        # Perform topological sort of equations based on dependencies
        self.equations_sorted, self.equations_graph, self.control_variables = (
            sort_equations(equations_dict, return_graph=True)
        )

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
        """

        if simulation_model is None:
            # Create a SimulationObjectModel object that will be used to run the simulation
            simulation_model = SimulationObjectModel(self.concrete_model)

        n_timesteps = len(self.concrete_model.t)
        n_regions = len(self.concrete_model.regions)

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
                # If no relative abatement is provided, set it to zero
                value = 0

            # TODO: check if variable is region/time dependent
            # First check if it is given as a dictionary with (time, region) keys
            if isinstance(value, dict):
                # Convert the dictionary to a numpy array
                value = self._dict_values_to_numpy(value)
            # If it is a single float value, convert it to a numpy array
            elif isinstance(value, (int, float)):
                value = np.full((n_timesteps, n_regions), value)

            # Check that the dimensions are correct
            assert value.shape == (n_timesteps, n_regions), (
                f"{var} must be of shape (n_timesteps, n_regions), "
                f"but is {value.shape}."
            )

            # Set the relative abatement for all regions and time periods
            getattr(simulation_model, var).values = value

        self._simulate(simulation_model)

        return simulation_model

    def find_prerun_bestguess(self):

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

    def _simulate(self, sim_m: SimulationObjectModel):
        """
        Given a SimulationModel object, evaluates all equations for every timestep
        """
        # First make sure simulation uses numpy-indices:
        sim_m.set_index_numpy_index()
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
        # Set indices back to original names ('CAN', 'WEU', ...)
        sim_m.set_index_names()

    def _dict_values_to_numpy(self, d):
        """
        Converts a dictionary of values to a numpy array.
        The keys of the dictionary should be tuples of (time, region).
        """
        arr = np.array(
            [
                [d[(t, r)] for r in self.concrete_model.regions]
                for t in self.concrete_model.t
            ]
        )
        return arr
