"""
Creates the class MIMOSA:
This is the main class. It builds a new AbstractModel
using the chosen damage and objective modules, then reads in the
parameter values and data (from the DataStore). With these values,
it creates an `instance` of the AbstractModel. This is then sent to the solver.
Finally, the export functions are called here.
"""

from typing import Any, Optional

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
from mimosa.core.simulation import Simulator, SimulationObjectModel


class MIMOSA:
    """
    Build and run a MIMOSA model.

    Creating this object checks and parses the configuration, builds the selected
    model components, loads their data and creates a Pyomo concrete model.

    Args:
        params: Configuration dictionary, normally created with
            `mimosa.load_params()`. Change its values before creating the model.
        prerun: If `True`, prepare the simulator, calculate an initial guess for
            optimisation and store a no-policy damage baseline. Disable this when
            only the constructed model is needed or when model construction time is
            more important than the initial guess.

    Attributes:
        concrete_model: Instantiated Pyomo model used for optimisation.
        equations: Equations available to simulation mode.
        model_context: Selected model components and their model options.
        simulator: Simulator associated with this model.
        status: Solver status after `solve()`; `None` before a solve starts.

    """

    concrete_model: ConcreteModel
    equations: list
    _params: dict

    def __init__(self, params: dict, prerun: bool = True) -> None:
        # Check if input parameter dictionary is valid
        self.preprocessor = Preprocessor(params)
        self.solver = Solver()
        self.simulator = Simulator()

        self.build_model()

        self.status = None  # Not started yet
        self.last_saved_filename = None  # Nothing saved yes
        self.last_saved_simulation_filename = None  # Nothing saved yes
        self._extra_constraints_added = False

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
        result = self.preprocessor.build_model()
        self.concrete_model = result.concrete_model
        self._params = result.params
        self.equations = result.equations
        self.model_context = result.context

    def prepare_simulation(self):
        """
        Prepares the model for simulation mode: it gathers all the equations,
        checks for circular dependencies, and sorts the equations based on their
        dependencies.

        Note: run self.simulator.plot_dependency_graph() to visualise the dependencies
        between equations.
        """
        self.simulator.prepare_simulation(self.equations, self.concrete_model)

    @utils.timer("Prerunning the model in simulation mode")
    def prerun_simulation(self):
        """Runs a pre-run simulation to get a good initial guess for the optimisation."""

        if not self.simulator.is_prepared:
            self.prepare_simulation()

        sim_m_best_guess = self.simulator.find_prerun_bestguess()

        # Set the best guess as initial values for the concrete model
        self.simulator.initialize_pyomo_model(self.concrete_model, sim_m_best_guess)

    def run_simulation(
        self, **control_variables_kwargs: Any
    ) -> SimulationObjectModel:
        """
        Evaluate the model equations for supplied control variables.

        Every control variable that is omitted or set to `None` is set to zero.
        Available control names can be inspected with
        `model.simulator.control_variables`.

        Args:
            **control_variables_kwargs: Values for control variables, keyed by
                variable name. Each value can be a number applied to all indices,
                a NumPy array matching the variable's dimensions, a dictionary
                keyed like the Pyomo variable, or `None` for zero.

        Returns:
            SimulationObjectModel: Calculated simulation results.

        Raises:
            ValueError: If a supplied name is not a control variable.
            AssertionError: If an array has the wrong dimensions.
        """
        if not self.simulator.is_prepared:
            self.prepare_simulation()

        return self.simulator.run(**control_variables_kwargs)

    def run_nopolicy_baseline(self) -> SimulationObjectModel:
        """
        Run and store the no-policy reference used for avoided damages.

        All control variables are set to zero. The resulting damage costs are
        stored in the Pyomo model as `nopolicy_damage_costs` for subsequent policy
        runs.

        Returns:
            SimulationObjectModel: No-policy simulation results.
        """

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
    def solve(
        self, verbose: bool = True, use_neos: bool = False, **kwargs: Any
    ) -> None:
        """
        Optimise the Pyomo model locally with IPOPT or remotely through NEOS.

        Args:
            verbose: Print IPOPT output during a local solve.
            use_neos: Submit the model to NEOS instead of using local IPOPT.
            **kwargs: Solver-specific options. Local IPOPT accepts
                `halt_on_ampl_error`, `ipopt_maxiter` and `ipopt_output_file`.
                NEOS requires `neos_email` and optionally accepts `solver_name`.

        Raises:
            SolverException: If the solver does not finish with status `OK`.
        """
        self.status = None  # Not started yet

        if use_neos:
            results = self.solver.solve_neos(self.concrete_model, **kwargs)
        else:
            results = self.solver.solve_ipopt(
                self.concrete_model, verbose=verbose, **kwargs
            )
        self.status = results.solver.status

    def save(self, filename: Optional[str] = None, **kwargs: Any) -> None:
        """
        Save optimisation results and their configuration.

        This creates `<filename>.csv` and `<filename>.csv.params.json`.

        Args:
            filename: Base filename without an extension.
            **kwargs: Output options. `folder` selects the output directory and
                `hash_suffix=True` adds a configuration hash to the filename.

        Example:
            ```python
            model = MIMOSA(params)
            model.solve()
            model.save("run1")
            ```
        """
        self.last_saved_filename = filename
        logger.info("Saving to %s", filename)
        save_output_pyomo(self._params, self.concrete_model, filename, **kwargs)

    def save_simulation(
        self,
        simulation_obj: SimulationObjectModel,
        filename: str,
        **kwargs: Any,
    ) -> None:
        """
        Save simulation results and their configuration.

        This creates `<filename>.csv` and `<filename>.csv.params.json`.

        Args:
            simulation_obj: Results returned by `run_simulation()` or
                `run_nopolicy_baseline()`.
            filename: Base filename without an extension.
            **kwargs: Output options. `folder` selects the output directory and
                `hash_suffix=True` adds a configuration hash to the filename.

        Example:
            ```python
            model = MIMOSA(params)
            simulation = model.run_nopolicy_baseline()
            model.save_simulation(simulation, "nopolicy_baseline")
            ```
        """
        self.last_saved_simulation_filename = filename
        logger.info("Saving simulation to %s", filename)
        save_output(
            simulation_obj.all_vars_for_export(),
            self._params,
            simulation_obj,
            filename,
            scenario_type="simulation",
            **kwargs,
        )

    @property
    def params(self) -> dict:
        """
        dict: Parsed configuration used to construct the model.

        Changing this dictionary does not rebuild or update the existing model.
        """
        return self._params
