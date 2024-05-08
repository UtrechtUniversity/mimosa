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
    AbstractModel,
    ConcreteModel,
    TransformationFactory,
    SolverFactory,
    SolverManagerFactory,
    SolverStatus,
    value,
    OptSolver,
    data,
    regional_params,
    utils,
    logger,
)
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.export import save_output  # , visualise_ipopt_output
from mimosa.abstract_model import create_abstract_model
from mimosa.concrete_model.instantiate_params import InstantiatedModel
from mimosa.concrete_model import simulation_mode


class MIMOSA:
    """
    The MIMOSA object creates an AbstractModel, makes a Concrete instance
    out of it, solves it and saves the results.

    Args:
        params (dict): contains all Param values, and is based on `input/config.yaml`

    Attributes:
        params (dict)
        regions (dict): taken from params
        abstract_model (AbstractModel): the AbstractModel created using the chosen damage/objective modules
        data_store (DataStore): object used to access regional data from the input database
        m (ConcreteModel): concrete instance of `abstract_model`

    """

    def __init__(self, params: dict):
        # Check if input parameter dictionary is valid
        params, parser_tree = check_params(params, True)
        params = parse_param_values(params)
        self.params = params
        self.param_parser_tree = parser_tree
        self.regions = params["regions"]

        self.abstract_model = self.get_abstract_model()
        self.concrete_model = self.create_instance()
        self.status = None  # Not started yet
        self.last_saved_filename = None  # Nothing saved yes
        self.preprocessing()

    def get_abstract_model(self) -> AbstractModel:
        """
        Returns:
            AbstractModel: model corresponding to the damage/objective module combination
        """
        damage_module = self.params["model"]["damage module"]
        emissiontrade_module = self.params["model"]["emissiontrade module"]
        financialtransfer_module = self.params["model"]["financialtransfer module"]
        welfare_module = self.params["model"]["welfare module"]
        objective_module = self.params["model"]["objective module"]

        return create_abstract_model(
            damage_module,
            emissiontrade_module,
            financialtransfer_module,
            welfare_module,
            objective_module,
        )

    @utils.timer("Concrete model creation")
    def create_instance(self) -> ConcreteModel:
        """
        Creates the objects necessary for the concrete model:
          - Regional parameter store
          - Data store
        Using these, it transforms the AbstractModel into a ConcreteModel

        Returns:
            ConcreteModel: model instantiated with parameter values and data functions
        """

        # Create the regional parameter store
        self.regional_param_store = regional_params.RegionalParamStore(
            self.params, self.param_parser_tree
        )

        # Create the data store
        self.data_store = data.DataStore(self.params)

        # Using these help objects, create the instantiated model
        instantiated_model = InstantiatedModel(
            self.abstract_model, self.regional_param_store, self.data_store
        )
        m = instantiated_model.concrete_model

        # When using simulation mode, add extra constraints to variables and disable other constraints
        if (
            self.params.get("simulation") is not None
            and self.params["simulation"]["simulationmode"]
        ):
            simulation_mode.set_simulation_mode(m, self.params)

        return m

    def preprocessing(self) -> None:
        """
        Pyomo can apply certain pre-processing steps before sending the model
        to the solver. These include:
          - Aggregate variables that are linked by equality constraints
          - Initialise non-fixed variables to midpoint of their boundaries
          - Fix variables that are de-facto fixed
          - Propagate variable fixing for equalities of type x = y
        """

        if len(self.regions) > 1:
            TransformationFactory("contrib.aggregate_vars").apply_to(
                self.concrete_model
            )
        TransformationFactory("contrib.init_vars_midpoint").apply_to(
            self.concrete_model
        )
        TransformationFactory("contrib.detect_fixed_vars").apply_to(self.concrete_model)
        if len(self.regions) > 1:
            TransformationFactory("contrib.propagate_fixed_vars").apply_to(
                self.concrete_model
            )

    def postprocessing(self) -> None:
        """Post-processing tasks to restore aggregate variables in pre-processing step"""
        if len(self.regions) > 1:
            TransformationFactory("contrib.aggregate_vars").update_variables(
                self.concrete_model
            )

    @utils.timer("Model solve", True)
    def solve(
        self,
        verbose=True,
        halt_on_ampl_error="no",
        use_neos=False,
        neos_email=None,
        ipopt_output_file=None,
        ipopt_maxiter=None,
    ) -> None:
        """Sends the concrete model to a solver.

        Args:
            verbose (bool, optional): Prints intermediate IPOPT results. Defaults to True.
            halt_on_ampl_error (str, optional): Lets IPOPT stop when invalid values are encountered. Defaults to "no".
            use_neos (bool, optional): Uses the external NEOS server for solving. Defaults to False.
            neos_email (str or None, optional): E-mail address for NEOS server. Defaults to None.
            ipopt_output_file (str or None, optional): Filename for IPOPT intermediate output. Defaults to None.
            ipopt_maxiter (int or None, optional): Maximum number of iterations for IPOPT. If None, use IPOPT defaults.

        Raises:
            SolverException: raised if solver did not exit with status OK
        """
        self.status = None  # Not started yet

        if use_neos:
            # Send concrete model to external solver on NEOS server
            # Requires authenticated email address
            os.environ["NEOS_EMAIL"] = neos_email
            solver_manager = SolverManagerFactory("neos")
            solver = "ipopt"  # or "conopt'
            results = solver_manager.solve(self.concrete_model, opt=solver)
        else:
            # Solve locally using ipopt
            opt: OptSolver = SolverFactory("ipopt")
            opt.options["halt_on_ampl_error"] = halt_on_ampl_error
            if ipopt_maxiter is not None:
                opt.options["max_iter"] = ipopt_maxiter
            if ipopt_output_file is not None:
                opt.options["output_file"] = ipopt_output_file
            results = opt.solve(
                self.concrete_model, tee=verbose, symbolic_solver_labels=True
            )
            # if ipopt_output_file is not None:
            #     visualise_ipopt_output(ipopt_output_file)

        self.postprocessing()

        logger.info("Status: {}".format(results.solver.status))

        self.status = results.solver.status

        if results.solver.status != SolverStatus.ok:
            if results.solver.status == SolverStatus.warning:
                warning_message = "MIMOSA did not solve succesfully. Status: {}, termination condition: {}".format(
                    results.solver.status, results.solver.termination_condition
                )
                logger.error(warning_message)
                raise SolverException(warning_message, utils.MimosaSolverWarning)
            if results.solver.status != SolverStatus.warning:
                raise SolverException(
                    f"Solver did not exit with status OK: {results.solver.status}"
                )

        logger.info(
            "Final NPV: {}".format(
                value(self.concrete_model.NPV[self.concrete_model.tf])
            )
        )

    def save(self, filename=None, **kwargs):
        self.last_saved_filename = filename
        save_output(self.params, self.concrete_model, filename, **kwargs)


###########################
##
## Utils
##
###########################


class SolverException(Exception):
    """Raised when Pyomo solver does not exit with status OK"""
