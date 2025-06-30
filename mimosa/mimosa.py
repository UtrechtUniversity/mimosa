"""
Creates the class MIMOSA:
This is the main class. It builds a new AbstractModel
using the chosen damage and objective modules, then reads in the
parameter values and data (from the DataStore). With these values,
it creates an `instance` of the AbstractModel. This is then sent to the solver.
Finally, the export functions are called here.
"""

from mimosa.common import (
    utils,
    logger,
    add_constraint,
    ConcreteModel,
)
from mimosa.export import save_output_pyomo, save_output  # , visualise_ipopt_output
from mimosa.components.after_initialisation import avoided_damages
from mimosa.core import simulation

from mimosa.core.initializer import Preprocessor
from mimosa.core.solver import Solver
from mimosa.core.simulation import Simulator


class MIMOSA:
    """
    The MIMOSA object creates an AbstractModel, makes a Concrete instance
    out of it, solves it and saves the results.

    Args:
        params (dict): contains all Param values, and is based on `input/config.yaml`
        prerun (bool): if True, runs a pre-run simulation to get a good initial guess for the optimisation.

    Attributes:
        concrete_model (ConcreteModel): initialised Pyomo model
        equations (list): list of equations (not constraints) used for simulation mode

    """

    concrete_model: ConcreteModel
    equations: list
    _params: dict

    def __init__(self, params: dict, prerun=True):
        # Check if input parameter dictionary is valid
        self.preprocessor = Preprocessor(params)
        self.solver = Solver()
        self.simulator = Simulator()

        self.build_model()

        self.status = None  # Not started yet
        self.last_saved_filename = None  # Nothing saved yes
        self.last_saved_simulation_filename = None  # Nothing saved yes

        if prerun:
            # Check if simulation mode is possible. If yes, perform a pre-run
            # simulation to get a good initial guess for the optimisation.
            try:
                self.prepare_simulation()
                self.prerun_simulation()
                self.run_nopolicy_baseline()
            except simulation.CircularDependencyError as e:
                logger.warning(
                    "Model will not be pre-ran with best guess simulation run: %s",
                    str(e),
                )

    @utils.timer("Model creation")
    def build_model(self):
        """
        Checks parameters for validity, creates the model and initializes it with data.
        """
        self.concrete_model, self._params, self.equations = (
            self.preprocessor.build_model()
        )

    def prepare_simulation(self):
        """
        Prepares the model for simulation mode: it gathers all the equations,
        checks for circular dependencies, and sorts the equations based on their
        dependencies.

        Note: run self.simulator.plot_dependency_graph() to visualise the dependencies
        between equations.
        """
        self.simulator.prepare_simulation(self.equations, self.concrete_model)

        # Set a flag to indicate that extra constraints have not been added yet
        self._extra_constraints_added = False

    @utils.timer("Prerunning the model in simulation mode")
    def prerun_simulation(self):
        """Runs a pre-run simulation to get a good initial guess for the optimisation."""

        sim_m_best_guess = self.simulator.find_prerun_bestguess()

        # Set the best guess as initial values for the concrete model
        self.simulator.initialize_pyomo_model(self.concrete_model, sim_m_best_guess)

    def run_simulation(self, relative_abatement=None):
        """
        Runs MIMOSA as simulation.

        It first sets the "free" variables (relative_abatement), then runs the simulation.

        Args:
            relative_abatement (array of n_timesteps x n_regions):
                Relative abatement values for each region and time step.
                If None, it defaults to a zero abatement scenario.
        """
        return self.simulator.run(relative_abatement)

    def run_nopolicy_baseline(self):
        """Runs the no-policy baseline simulation with relative abatement set to 0."""

        # Run simulator with default relative abatement set to 0
        nopolicy_baseline = self.run_simulation()

        # Store the no-policy baseline damage costs in the concrete model
        m = self.concrete_model
        if not self._extra_constraints_added:
            for constraint in avoided_damages.get_constraints(m):
                add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)
            self._extra_constraints_added = True

        m.nopolicy_damage_costs.store_values(
            nopolicy_baseline.damage_costs.get_all_indexed()
        )

        return nopolicy_baseline

    @utils.timer("Model solve", True)
    def solve(self, verbose=True, use_neos=False, **kwargs) -> None:
        """Sends the model to a solver.
        Raises:
            SolverException: raised if solver did not exit with status OK
        """
        self.status = None  # Not started yet

        if use_neos:
            results = self.solver.solve_neos(self.concrete_model, **kwargs)
        else:
            results = self.solver.solve_ipopt(
                self.concrete_model, verbose=verbose, **kwargs
            )
        self.status = results.solver.status

    def save(self, filename=None, **kwargs):
        """
        Saves the MIMOSA optimisation results to a file.

        Args:
            filename (str): The filename to save the results to.

        Example usage:
            model = MIMOSA(params)
            model.solve()
            model.save("run1")
        """
        self.last_saved_filename = filename
        save_output_pyomo(self._params, self.concrete_model, filename, **kwargs)

    def save_simulation(self, simulation_obj, filename, **kwargs):
        """
        Saves the simulation results to a file.

        Args:
            simulation_obj (SimulationObjectModel): The simulation results to save.
            filename (str): The filename to save the results to.

        Example usage:
            model = MIMOSA(params)
            simulation = model.run_nopolicy_baseline()
            model.save_simulation(simulation, "nopolicy_baseline")
        """
        self.last_saved_simulation_filename = filename
        save_output(
            simulation_obj.all_vars_for_export(),
            self._params,
            simulation_obj,
            filename,
            scenario_type="simulation",
            **kwargs
        )

    @property
    def params(self):
        """
        Returns the parsed parameters used to create the model.

        Note that the params cannot be changed after the model has been created.
        """
        return self._params
