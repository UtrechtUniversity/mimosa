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

from glob import glob
import pandas as pd
from model.common import RegionalConstraint, ConcreteModel, add_constraint


def set_simulation_mode(m: ConcreteModel, params: dict) -> None:
    # Add constraints for each fixed variable
    _set_constraints_fixed_variables(m, params)

    # Disable constraints to allow feasible solution
    _deactivate_constraints(m, params)


def _set_constraints_fixed_variables(m, params):

    data_cache = {}
    extra_constraints = []

    for variable_name, filepath in params["simulation"]["constraint_variables"].items():
        extra_constraints.extend(
            _fixed_data_constraint(variable_name, filepath, data_cache)
        )

    # Add constraints to concrete model
    for constraint in extra_constraints:
        add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)


def _fixed_data_constraint(variable_name, filepath, data_cache):
    # 1. Read datafile
    if filepath not in data_cache:
        data_cache[filepath] = _read_csv(filepath)
    imported_data = data_cache[filepath]

    # 2. Select data
    fixed_data = imported_data[imported_data["Variable"] == variable_name]
    fixed_data = fixed_data.drop(columns="Variable").set_index("Region")

    # 3. Create constraints out of this
    eps = 1e-3  # TODO make eps a variable

    # TODO allow for global constraints here
    extra_constraints = [
        RegionalConstraint(
            lambda m, t, r: getattr(m, variable_name)[t, r]
            - fixed_data.loc[r, str(int(m.year(t)))]
            <= eps
        ),
        RegionalConstraint(
            lambda m, t, r: getattr(m, variable_name)[t, r]
            - fixed_data.loc[r, str(int(m.year(t)))]
            >= -eps
        ),
    ]

    return extra_constraints


def _deactivate_constraints(m, params):
    if params["simulation"]["deactivated_constraints"] is not None:
        for constraint_name in params["simulation"]["deactivated_constraints"]:
            constraint = getattr(m, f"constraint_{constraint_name}")
            if constraint is not None:
                constraint.deactivate()


##########
# Utils
##########


def _read_csv(path):
    if "*" in path:
        path = glob(path)[0]
    return pd.read_csv(path)
