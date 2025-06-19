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
        self.equations_sorted, self.equations_graph = sort_equations(
            equations_dict, return_graph=True
        )

    def run(
        self,
        relative_abatement=None,
        simulation_model=None,
    ):
        """
        Runs MIMOSA as simulation.

        It first sets the "free" variables (relative_abatement), then runs the simulation

        Args:
            relative_abatement (array of n_timesteps x n_regions):
                Relative abatement values for each region and time step.
                If None, it defaults to a zero abatement scenario.
        """

        n_timesteps = len(self.concrete_model.t)
        n_regions = len(self.concrete_model.regions)

        # TODO: make dynamic list of "free" variables
        # For now, we only have relative_abatement as a free variable

        if relative_abatement is None:
            # If no relative abatement is provided, set it to zero
            relative_abatement = np.zeros((n_timesteps, n_regions))
        else:
            # First check if it is given as a dictionary with (time, region) keys
            if isinstance(relative_abatement, dict):
                # Convert the dictionary to a numpy array
                relative_abatement = self._dict_values_to_numpy(relative_abatement)
            # Check that the dimensions are correct
            assert relative_abatement.shape == (n_timesteps, n_regions), (
                f"relative_abatement must be of shape (n_timesteps, n_regions), "
                f"but is {relative_abatement.shape}."
            )

        if simulation_model is None:
            # Create a SimulationObjectModel object that will be used to run the simulation
            simulation_model = SimulationObjectModel(self.concrete_model)

        # Set the relative abatement for all regions and time periods
        simulation_model.relative_abatement.values = relative_abatement

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
            self.run(relative_abatement, sim_m)
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
