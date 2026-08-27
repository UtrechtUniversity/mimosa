"""
Creates the class MIMOSA:
This is the main class. It builds a new AbstractModel
using the chosen damage and objective modules, then reads in the
parameter values and data (from the DataStore). With these values,
it creates an `instance` of the AbstractModel. This is then sent to the solver.
Finally, the export functions are called here.
"""

import time
from copy import deepcopy
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
        solve_runtime: Wall-clock duration of the most recently completed
            `solve()` call in seconds; `None` before a solve completes.
        workflow_control_values: Controls transferred by the most recent
            sequential workflow; `None` for an ordinary solve.

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
        self.solve_runtime = None  # No completed solve has been timed yet
        self.workflow_control_values = None
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
            SimulationObjectModel: Calculated simulation results. Its `runtime`
                attribute contains the wall-clock duration of this call in seconds.

        Raises:
            ValueError: If a supplied name is not a control variable.
            AssertionError: If an array has the wrong dimensions.
        """
        start_time = time.perf_counter()

        if not self.simulator.is_prepared:
            self.prepare_simulation()

        simulation_obj = self.simulator.run(**control_variables_kwargs)
        simulation_obj.runtime = time.perf_counter() - start_time
        simulation_obj.params = self._params
        return simulation_obj

    def run_nopolicy_baseline(self) -> SimulationObjectModel:
        """
        Run and store the no-policy reference used for avoided damages.

        Mitigation and adaptation are both disabled. The resulting damage costs
        are stored in the Pyomo model as `nopolicy_damage_costs` for subsequent
        policy runs. An ACCREU model with analytical adaptation uses a temporary
        no-adaptation model for this reference.

        Returns:
            SimulationObjectModel: No-policy simulation results.
        """

        nopolicy_baseline = self._run_nopolicy_baseline_simulation()

        # Store the no-policy baseline damage costs in the concrete model
        m = self.concrete_model
        added_avoided_damage_equations = False
        if not self._extra_constraints_added:
            avoided_damage_equations = avoided_damages.get_constraints(m)
            for equation in avoided_damage_equations:
                add_constraint(m, equation.to_pyomo_constraint(m), equation.name)
            self.equations.extend(avoided_damage_equations)
            self._extra_constraints_added = True
            added_avoided_damage_equations = True

        m.nopolicy_damage_costs.store_values(
            nopolicy_baseline.damage_costs.get_all_indexed()
        )

        # Avoided damages are added only after the baseline is available. Include
        # their equations in subsequent simulation runs as well as in Pyomo solves.
        if added_avoided_damage_equations:
            self.prepare_simulation()

        return nopolicy_baseline

    def _run_nopolicy_baseline_simulation(self) -> SimulationObjectModel:
        """Evaluate a reference without mitigation or analytical adaptation."""

        if not self._uses_analytical_accreu_adaptation():
            return self.run_simulation()

        baseline_params = deepcopy(self._params)
        baseline_options = baseline_params["model structure"][
            "damage module options"
        ]
        baseline_options["ACCREU_adaptation"] = "noadaptation"
        baseline_options["ACCREU_adaptation_determination"] = "solver_control"
        baseline_options["ACCREU_CBA_strategy"] = "joint"

        baseline_model = MIMOSA(baseline_params, prerun=False)
        return baseline_model.run_simulation()

    @utils.timer("Model solve", True, store_as="solve_runtime")
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
        self.solve_runtime = None  # Do not retain timing from an earlier solve
        self.workflow_control_values = None

        if self._uses_sequential_accreu_cba():
            self._solve_accreu_mitigation_then_adaptation(
                verbose=verbose, use_neos=use_neos, **kwargs
            )
        else:
            self._solve_model_normally(verbose=verbose, use_neos=use_neos, **kwargs)

    def _solve_model_normally(
        self, verbose: bool = True, use_neos: bool = False, **kwargs: Any
    ) -> None:
        """Run one ordinary optimisation without workflow orchestration."""

        if use_neos:
            results = self.solver.solve_neos(self.concrete_model, **kwargs)
        else:
            results = self.solver.solve_ipopt(
                self.concrete_model, verbose=verbose, **kwargs
            )
        self.status = results.solver.status

    def _uses_sequential_accreu_cba(self) -> bool:
        """Return whether this model selects the ordered ACCREU CBA workflow."""

        if (
            self.model_context.module("damage") != "ACCREU"
            or self.model_context.option("damage", "ACCREU_adaptation")
            == "noadaptation"
        ):
            return False

        strategy = self.model_context.option("damage", "ACCREU_CBA_strategy")
        determination = self.model_context.option(
            "damage", "ACCREU_adaptation_determination"
        )
        required_determination = (
            "analytical_optimum"
            if strategy == "mitigation_then_adaptation"
            else "solver_control"
        )
        if determination != required_determination:
            raise ValueError(
                f"ACCREU_CBA_strategy='{strategy}' requires "
                "ACCREU_adaptation_determination="
                f"'{required_determination}', not '{determination}'."
            )

        return strategy == "mitigation_then_adaptation"

    def _uses_analytical_accreu_adaptation(self) -> bool:
        """Return whether ACCREU adaptation is defined analytically."""

        return (
            self.model_context.module("damage") == "ACCREU"
            and self.model_context.option("damage", "ACCREU_adaptation")
            != "noadaptation"
            and self.model_context.option(
                "damage", "ACCREU_adaptation_determination"
            )
            == "analytical_optimum"
        )

    def _solve_accreu_mitigation_then_adaptation(
        self, verbose: bool = True, use_neos: bool = False, **kwargs: Any
    ) -> None:
        """Optimise mitigation first, then evaluate analytical adaptation."""

        if self._params["emissions"]["carbonbudget"] is not False:
            raise ValueError(
                "ACCREU_CBA_strategy='mitigation_then_adaptation' is only "
                "available for cost-benefit analysis without a fixed carbon budget. "
                "Use ACCREU_CBA_strategy='joint' with "
                "ACCREU_adaptation_determination='solver_control' for a "
                "carbon-budget run."
            )

        mitigation_params = deepcopy(self._params)
        mitigation_options = mitigation_params["model structure"][
            "damage module options"
        ]
        mitigation_options["ACCREU_adaptation"] = "noadaptation"
        mitigation_options["ACCREU_CBA_strategy"] = "joint"
        mitigation_options["ACCREU_adaptation_determination"] = "solver_control"

        mitigation_model = MIMOSA(mitigation_params)
        mitigation_model.solve(verbose=verbose, use_neos=use_neos, **kwargs)

        control_values = self._extract_compatible_controls(mitigation_model)
        final_result = self.run_simulation(**control_values)
        self.simulator.initialize_pyomo_model(self.concrete_model, final_result)

        self.workflow_control_values = control_values
        self.status = mitigation_model.status

    def _extract_compatible_controls(self, source_model: "MIMOSA") -> dict:
        """Extract controls after validating replay compatibility."""

        if not source_model.simulator.is_prepared:
            source_model.prepare_simulation()
        if not self.simulator.is_prepared:
            self.prepare_simulation()

        source_controls = set(source_model.simulator.control_variables)
        target_controls = set(self.simulator.control_variables)
        if source_controls != target_controls:
            raise ValueError(
                "Cannot transfer controls between ACCREU CBA stages: "
                f"source controls are {sorted(source_controls)}, while target "
                f"controls are {sorted(target_controls)}."
            )

        for index_name in ("t", "regions"):
            source_values = tuple(
                getattr(source_model.concrete_model, index_name).ordered_data()
            )
            target_values = tuple(
                getattr(self.concrete_model, index_name).ordered_data()
            )
            if source_values != target_values:
                raise ValueError(
                    "Cannot transfer controls between ACCREU CBA stages: "
                    f"the {index_name} indices are incompatible."
                )

        control_values = {}
        for name in sorted(target_controls):
            source_values = getattr(
                source_model.concrete_model, name
            ).extract_values()
            target_keys = set(getattr(self.concrete_model, name).extract_values())
            if set(source_values) != target_keys:
                raise ValueError(
                    "Cannot transfer control "
                    f"'{name}' between ACCREU CBA stages: its indices are incompatible."
                )
            control_values[name] = source_values

        return control_values

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
        save_output_pyomo(
            self._params,
            self.concrete_model,
            filename,
            runtime=self.solve_runtime,
            **kwargs,
        )

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
            getattr(simulation_obj, "params", None) or self._params,
            simulation_obj,
            filename,
            scenario_type="simulation",
            runtime=simulation_obj.runtime,
            **kwargs,
        )

    @property
    def params(self) -> dict:
        """
        dict: Parsed configuration used to construct the model.

        Changing this dictionary does not rebuild or update the existing model.
        """
        return self._params
