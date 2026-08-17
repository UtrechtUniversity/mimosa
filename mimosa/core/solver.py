import os
from pyomo.common.collections import ComponentSet
from pyomo.core.expr.visitor import identify_variables
from pyomo.environ import Constraint, Objective, TransformationFactory

from mimosa.common import (
    SolverFactory,
    SolverManagerFactory,
    SolverStatus,
    OptSolver,
    logger,
    utils,
)


class Solver:
    """
    Provides various methods to solve a MIMOSA model using different solvers.
    """

    def __init__(self):
        self.status = None

    def solve_ipopt(
        self,
        concrete_model,
        verbose=True,
        halt_on_ampl_error="no",
        ipopt_maxiter=None,
        ipopt_output_file=None,
    ):
        """
        Solves the given concrete model using the IPOPT solver.

        Args:
            concrete_model: The Pyomo ConcreteModel to solve.
            verbose: If True, prints solver output.
            halt_on_ampl_error: If True, halts on AMPL errors.
            ipopt_maxiter: Maximum number of iterations for IPOPT.
            ipopt_output_file: File to write IPOPT output to.

        Raises:
            SolverException if solver status is not "OK"
        """

        # _deactivate_trivial_constraints_if_required(concrete_model)

        # Create an IPOPT solver instance
        opt: OptSolver = SolverFactory("ipopt")
        opt.options["halt_on_ampl_error"] = halt_on_ampl_error
        if ipopt_maxiter is not None:
            opt.options["max_iter"] = ipopt_maxiter
        if ipopt_output_file is not None:
            opt.options["output_file"] = ipopt_output_file

        # Solve the model
        results = opt.solve(concrete_model, tee=verbose, symbolic_solver_labels=True)

        self._log_status(results)

        return results

    def solve_neos(self, concrete_model, neos_email, solver_name="ipopt"):
        """
        Solves the given concrete model using NEOS server.

        Args:
            concrete_model: The Pyomo ConcreteModel to solve.
            neos_email: Email address for NEOS server.
            solver_name: Name of the solver to use on NEOS (default is 'ipopt').

        Raises:
            SolverException if solver status is not "OK"
        """
        os.environ["NEOS_EMAIL"] = neos_email
        solver_manager = SolverManagerFactory("neos")
        results = solver_manager.solve(concrete_model, opt=solver_name)

        self._log_status(results)

        return results

    def _log_status(self, results):
        """
        Logs the status of the solver results.
        If status is not OK, raises a SolverException
        """
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


###########################
##
## Utils
##
###########################


class SolverException(Exception):
    """Raised when Pyomo solver does not exit with status OK"""


def _deactivate_trivial_constraints_if_required(model):
    """Remove constant constraints only when IPOPT would reject the model.

    Fixed-variable propagation can leave satisfied constant equalities active.
    Usually these are harmless, and removing them can adversely change sparse
    solver ordering. If active equalities outnumber the unfixed variables that
    occur in the optimization problem, however, IPOPT refuses to start. In that
    case deactivating verified trivial constraints restores the true structural
    degrees of freedom.
    """

    relevant_variables = ComponentSet()
    active_equalities = 0

    for constraint in model.component_data_objects(Constraint, active=True):
        if constraint.equality:
            active_equalities += 1
        relevant_variables.update(
            variable
            for variable in identify_variables(constraint.body, include_fixed=False)
            if not variable.fixed
        )

    for objective in model.component_data_objects(Objective, active=True):
        relevant_variables.update(
            variable
            for variable in identify_variables(objective.expr, include_fixed=False)
            if not variable.fixed
        )

    if len(relevant_variables) < active_equalities:
        TransformationFactory("contrib.deactivate_trivial_constraints").apply_to(model)
