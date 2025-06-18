import os
from mimosa.common import (
    SolverFactory,
    SolverManagerFactory,
    SolverStatus,
    OptSolver,
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
        """

        # Create an IPOPT solver instance
        opt: OptSolver = SolverFactory("ipopt")
        opt.options["halt_on_ampl_error"] = halt_on_ampl_error
        if ipopt_maxiter is not None:
            opt.options["max_iter"] = ipopt_maxiter
        if ipopt_output_file is not None:
            opt.options["output_file"] = ipopt_output_file

        # Solve the model
        results = opt.solve(concrete_model, tee=verbose, symbolic_solver_labels=True)

        # Check the solver status
        self.status = results.solver.status
        if self.status != SolverStatus.ok:
            raise Exception(f"Solver did not exit with status OK: {self.status}")

        return results

    def solve_neos(self, concrete_model, neos_email, solver_name="ipopt"):
        """
        Solves the given concrete model using NEOS server.

        Args:
            concrete_model: The Pyomo ConcreteModel to solve.
            neos_email: Email address for NEOS server.
            solver_name: Name of the solver to use on NEOS (default is 'ipopt').
        """
        os.environ["NEOS_EMAIL"] = neos_email
        solver_manager = SolverManagerFactory("neos")
        results = solver_manager.solve(concrete_model, opt=solver_name)
        return results
