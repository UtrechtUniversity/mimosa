"""
Creates the class MIMOSA:
This is the main class. It builds a new AbstractModel
using the chosen damage and objective modules, then reads in the
parameter values and data (from the DataStore). With these values,
it creates an `instance` of the AbstractModel. This is then sent to the solver.
Finally, the export functions are called here.
"""

import os

from model.common import (
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
    units,
)
from model.export import full_plot, visualise_ipopt_output, save_output
from model.abstract_model import create_abstract_model
from model.concrete_model.instantiate_params import InstantiatedModel
from model.concrete_model import simulation_mode


class MIMOSA:
    """
    The MIMOSA object creates an AbstractModel, makes a Concrete instance
    out of it, solves it and saves the results.

    Args:
        params (dict): contains all Param values, and is based on `input/config.yaml`

    Attributes:
        params (dict)
        regions (dict): taken from params
        quant (Quantity): callable object used to parse and convert quantities with units
        abstract_model (AbstractModel): the AbstractModel created using the chosen damage/objective modules
        data_store (DataStore): object used to access regional data from the input database
        m (ConcreteModel): concrete instance of `abstract_model`

    """

    def __init__(self, params: dict):
        self.params = params
        self.regions = params["regions"]

        self.abstract_model = self.get_abstract_model()
        self.concrete_model = self.create_instance()
        self.preparation()

    def get_abstract_model(self) -> AbstractModel:
        """
        Returns:
            AbstractModel: model corresponding to the damage/objective module combination
        """
        damage_module = self.params["model"]["damage module"]
        objective_module = self.params["model"]["objective module"]

        return create_abstract_model(damage_module, objective_module)

    @utils.timer("Concrete model creation")
    def create_instance(self) -> ConcreteModel:

        # Create a Quantity object for automatic unit handling
        self.quant = units.Quantity(self.params)

        # Create the regional parameter store
        self.regional_param_store = regional_params.RegionalParamStore(self.params)

        # Create the data store
        self.data_store = data.DataStore(
            self.params, self.quant, self.regional_param_store
        )

        # Using these help objects, create the instantiated model
        instantiated_model = InstantiatedModel(
            self.abstract_model, self.regional_param_store, self.data_store, self.quant
        )
        m = instantiated_model.concrete_model

        # When using simulation mode, add extra constraints to variables and disable other constraints
        if (
            self.params.get("simulation") is not None
            and self.params["simulation"]["simulationmode"]
        ):
            simulation_mode.set_simulation_mode(m, self.params)

        return m

    def preparation(self) -> None:

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

    @utils.timer("Model solve")
    def solve(
        self,
        verbose=False,
        halt_on_ampl_error="no",
        use_neos=False,
        neos_email=None,
        ipopt_output_file=None,
    ) -> None:
        if use_neos:
            os.environ["NEOS_EMAIL"] = neos_email
            solver_manager = SolverManagerFactory("neos")
            solver = "conopt"  # 'ipopt'
            results = solver_manager.solve(self.concrete_model, opt=solver)
        else:
            opt: OptSolver = SolverFactory("ipopt")
            opt.options["halt_on_ampl_error"] = halt_on_ampl_error
            opt.options["output_file"] = ipopt_output_file
            results = opt.solve(
                self.concrete_model, tee=verbose, symbolic_solver_labels=True
            )
            if ipopt_output_file is not None:
                visualise_ipopt_output(ipopt_output_file)

        # Restore aggregated variables
        if len(self.regions) > 1:
            TransformationFactory("contrib.aggregate_vars").update_variables(
                self.concrete_model
            )

        if results.solver.status != SolverStatus.ok:
            print(
                "Status: {}, termination condition: {}".format(
                    results.solver.status, results.solver.termination_condition
                )
            )
            if results.solver.status != SolverStatus.warning:
                raise Exception("Solver did not exit with status OK")

        print("Final NPV:", value(self.concrete_model.NPV[self.concrete_model.tf]))

    @utils.timer("Plotting results")
    def plot(self, filename="result", **kwargs):
        full_plot(self.concrete_model, filename, **kwargs)

    def save(self, experiment=None, **kwargs):
        save_output(self.params, self.concrete_model, experiment, **kwargs)
