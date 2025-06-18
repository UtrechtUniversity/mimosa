"""
Creates the class MIMOSA:
This is the main class. It builds a new AbstractModel
using the chosen damage and objective modules, then reads in the
parameter values and data (from the DataStore). With these values,
it creates an `instance` of the AbstractModel. This is then sent to the solver.
Finally, the export functions are called here.
"""

import os
import warnings

from mimosa.common import (
    SolverFactory,
    SolverManagerFactory,
    SolverStatus,
    value,
    OptSolver,
    utils,
    logger,
    add_constraint,
    ConcreteModel,
)
from mimosa.export import save_output_pyomo, save_output  # , visualise_ipopt_output
from mimosa.components.after_initialisation import avoided_damages
from mimosa import simulation

from mimosa.core.initializer import Preprocessor
from mimosa.core.solver import Solver


class MIMOSA:
    """
    The MIMOSA object creates an AbstractModel, makes a Concrete instance
    out of it, solves it and saves the results.

    Args:
        params (dict): contains all Param values, and is based on `input/config.yaml`
        prerun (bool): if True, runs a pre-run simulation to get a good initial guess for the optimisation.

    Attributes:
        params (dict)
        regions (dict): taken from params
        abstract_model (AbstractModel): the AbstractModel created using the chosen damage/objective modules
        equations (list): list of equations (not constraints) used for simulation mode
        data_store (DataStore): object used to access regional data from the input database
        m (ConcreteModel): concrete instance of `abstract_model`

    """

    params: dict
    concrete_model: ConcreteModel
    equations: list

    def __init__(self, params: dict, prerun=True):
        # Check if input parameter dictionary is valid
        self.preprocessor = Preprocessor(params)
        self.solver = Solver()

        self.build_model()

        self.status = None  # Not started yet
        self.last_saved_filename = None  # Nothing saved yes

        self.equations_sorted = None  # Not created yet
        self.equations_graph = None  # Not created yet
        self.nopolicy_baseline = None
        if prerun:
            # Check if simulation mode is possible. If yes, perform a pre-run
            # simulation to get a good initial guess for the optimisation.
            try:
                self.prepare_simulation()
                self.prerun_simulation()
                self.run_nopolicy_baseline()
                self._add_extra_avoided_damages_constraints()
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
        self.concrete_model, self.params, self.equations = (
            self.preprocessor.build_model()
        )

    def prepare_simulation(self):
        """Prepares the model for simulation mode: it gathers all the equations,
        checks for circular dependencies, and sorts the equations based on their
        dependencies."""

        # Check the dependencies between variables and equations to test
        # if there are circular dependencies. If there are, it is not possible
        # to run in simulation mode.
        equations_dict = {eq.name: eq for eq in self.equations}
        simulation.calc_dependencies(equations_dict, self.concrete_model)
        # Perform topological sort of equations based on dependencies
        self.equations_sorted, self.equations_graph = simulation.sort_equations(
            equations_dict, return_graph=True
        )

    @utils.timer("Prerunning the model in simulation mode")
    def prerun_simulation(
        self,
        save_simulation=False,
        filename="run1_prerun_guess",
    ) -> None:

        sim_m_best_guess = simulation.find_prerun_bestguess(
            self.concrete_model, self.equations_sorted
        )
        # Set the best guess as initial values for the concrete model
        simulation.initialize_pyomo_model(self.concrete_model, sim_m_best_guess)

        # Save the best guess to a file
        if save_simulation:
            save_output(
                sim_m_best_guess.all_vars_for_export(),
                self.params,
                sim_m_best_guess,
                f"{filename}_simulation_prerun",
            )

    @utils.timer("Calculating no-policy baseline in simulation mode")
    def run_nopolicy_baseline(self):

        m = self.concrete_model
        self.nopolicy_baseline = simulation.run_nopolicy_baseline(
            m, self.equations_sorted
        )

    def _add_extra_avoided_damages_constraints(self):

        m = self.concrete_model
        constraints = avoided_damages.get_constraints(m)
        for constraint in constraints:
            add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)

        m.nopolicy_damage_costs.store_values(
            self.nopolicy_baseline.damage_costs.get_all_indexed()
        )

    def plot_dependency_graph(self):
        """Plots the dependency graph of the equations."""
        if self.equations_graph is None:
            raise ValueError(
                "Dependency graph not created yet. Call prepare_simulation() first."
            )
        return simulation.plot_dependency_graph(self.equations_graph)

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

        self.preprocessor.postprocess(self.concrete_model)

        status = results.solver.status

        logger.info("Status: {}".format(status))

        self.status = status

        if status != SolverStatus.ok:
            if status == SolverStatus.warning:
                warning_message = "MIMOSA did not solve succesfully. Status: {}, termination condition: {}".format(
                    status, results.solver.termination_condition
                )
                logger.error(warning_message)
                raise SolverException(warning_message, utils.MimosaSolverWarning)
            if status != SolverStatus.warning:
                raise SolverException(f"Solver did not exit with status OK: {status}")

    def save(self, filename=None, with_nopolicy_baseline=False, **kwargs):
        self.last_saved_filename = filename
        save_output_pyomo(self.params, self.concrete_model, filename, **kwargs)

        if self.nopolicy_baseline is not None and with_nopolicy_baseline:
            save_output(
                self.nopolicy_baseline.all_vars_for_export(),
                None,
                self.nopolicy_baseline,
                f"{filename}.nopolicy_baseline",
            )


###########################
##
## Utils
##
###########################


class SolverException(Exception):
    """Raised when Pyomo solver does not exit with status OK"""
