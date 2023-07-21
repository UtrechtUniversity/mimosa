"""
The simulation mode imposes exogenously an emission path, carbon price or
other regional or global variable.

The extra constraints are defined in the params dict, under:
    params["simulation"]["constraint_variables"] = {
        'variablename1': 'path_of_outputfile_to_be_used.csv',
        ...
    }

At the same time, certain constraints can be deactivated. These are defined in:
    params["simulation"]["disabled_constraints"] = ['carbon_budget', ...]

"""

from mimosa.common import ConcreteModel
from .deactivate_constraints import deactivate_constraints
from .set_constraints import set_constraints_fixed_variables


def set_simulation_mode(m: ConcreteModel, params: dict) -> None:
    # Add constraints for each fixed variable
    set_constraints_fixed_variables(m, params)

    # Disable constraints to allow feasible solution
    deactivate_constraints(m, params)
