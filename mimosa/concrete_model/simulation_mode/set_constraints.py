"""
Add constraints for each fixed variable
"""

import pandas as pd
from mimosa.common import (
    RegionalConstraint,
    GlobalConstraint,
    has_time_and_region_dim,
    add_constraint,
    Constraint,
)
from .utils import InterpolatingData, read_csv


def set_constraints_fixed_variables(m, params):
    data_cache = {}
    extra_constraints = []

    for variable_name, filepath_or_data in params["simulation"][
        "constraint_variables"
    ].items():
        interp_data = _get_interp_data(filepath_or_data, data_cache, variable_name)
        extra_constraints.extend(_fixed_data_constraint(m, variable_name, interp_data))

    # Add constraints to concrete model
    for constraint in extra_constraints:
        add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)


def _get_interp_data(filepath_or_data, data_cache, variable_name):
    if isinstance(filepath_or_data, dict):
        data = pd.DataFrame(filepath_or_data)
        # Important: data should be a dataframe with years as columns and regions as row indices
        return InterpolatingData(data)

    # If it is a string, read the data from the CSV file
    filepath = filepath_or_data
    # 1. Read datafile
    if filepath not in data_cache:
        data_cache[filepath] = read_csv(filepath)
    imported_data = data_cache[filepath]

    # 2. Select data
    fixed_data = imported_data[imported_data["Variable"] == variable_name]
    fixed_data = fixed_data.drop(
        columns=["Variable", "Unit"], errors="ignore"
    ).set_index("Region")
    interp_data = InterpolatingData(fixed_data)
    return interp_data


def _fixed_data_constraint(m, variable_name, interp_data):
    # 3. Create constraints out of this
    eps = 1e-3  # TODO make eps a variable

    if has_time_and_region_dim(getattr(m, variable_name)):
        extra_constraints = _extra_regional_constraint(variable_name, interp_data, eps)
    else:
        extra_constraints = _extra_global_constraint(variable_name, interp_data, eps)

    return extra_constraints


###########
#
# Make regional or global constraints
#
############


def _extra_regional_constraint(variable_name, interp_data, eps):
    return [
        RegionalConstraint(
            lambda m, t, r: (
                getattr(m, variable_name)[t, r] - interp_data.get(r, m.year(t)) <= eps
                if interp_data.get(r, m.year(t)) is not None
                else Constraint.Skip
            )
            # if m.year(t) <= interp_data.maxyear
            # else Constraint.Skip
        ),
        RegionalConstraint(
            lambda m, t, r: (
                getattr(m, variable_name)[t, r] - interp_data.get(r, m.year(t)) >= -eps
                if interp_data.get(r, m.year(t)) is not None
                else Constraint.Skip
            )
            # if m.year(t) <= interp_data.maxyear
            # else Constraint.Skip
        ),
    ]


def _extra_global_constraint(variable_name, interp_data: InterpolatingData, eps):
    return [
        GlobalConstraint(
            lambda m, t: (
                getattr(m, variable_name)[t] - interp_data.get("Global", m.year(t))
                <= eps
                if interp_data.get("Global", m.year(t)) is not None
                else Constraint.Skip
            )
            # if t > 0  # and m.year(t) <= interp_data.maxyear
            # else Constraint.Skip
        ),
        GlobalConstraint(
            lambda m, t: (
                getattr(m, variable_name)[t] - interp_data.get("Global", m.year(t))
                >= -eps
                if interp_data.get("Global", m.year(t)) is not None
                else Constraint.Skip
            )
            # if t > 0  # and m.year(t) <= interp_data.maxyear
            # else Constraint.Skip
        ),
    ]
