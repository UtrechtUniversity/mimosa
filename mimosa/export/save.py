"""
Generates a CSV file with a row for each variable (`Var`)
in the ConcreteModel `m`.
"""

import json
import os
import hashlib
import numpy as np
import pandas as pd

import mimosa
from mimosa.common import Var, get_all_variables, get_all_time_dependent_params, value


def save_output_pyomo(
    params,
    m,
    filename="run1",
    hash_suffix=False,
    folder="output",
    solve_runtime=None,
):
    # 2. Save the Pyomo variables and data functions
    all_variables = get_all_variables(m) + get_all_time_dependent_params(m)
    save_output(
        all_variables,
        params,
        m,
        filename,
        "optimisation",
        hash_suffix,
        folder,
        solve_runtime=solve_runtime,
    )


def save_output(
    all_variables,
    params,
    m,
    filename,
    scenario_type="optimisation",
    hash_suffix=False,
    folder="output",
    solve_runtime=None,
):
    # 1. Create a unique identifier
    if hash_suffix:
        settings_hash = hashlib.md5(json.dumps(params).encode()).hexdigest()[:9]
    else:
        settings_hash = ""

    rows = []
    for useful_var in all_variables:
        var_to_row(rows, m, useful_var.var, useful_var.is_regional, useful_var.unit)
    add_derived_global_cost_rows(rows, m, all_variables)
    dataframe = rows_to_dataframe(rows, m)

    # add_param_columns(df, params, id, experiment)

    # 3. Save the CSV file
    os.makedirs(folder + "/", exist_ok=True)
    filename = f"{filename}_{settings_hash}" if hash_suffix else filename

    path = f"{folder}/{filename}.csv"
    dataframe.to_csv(path, float_format="%.6g", index=False)
    print(f"Saved to {path}")

    # 3. Save the param file
    if params is not None:
        # Add MIMOSA version
        params_with_version = {
            "MIMOSA version": mimosa.__version__,
            "Scenario type": scenario_type,
            **params,
        }
        if solve_runtime is not None:
            params_with_version["Runtime (seconds)"] = solve_runtime
        with open(f"{path}.params.json", "w") as fh:
            json.dump(params_with_version, fh)


def var_to_row(rows, m, var, is_regional, unit):
    # If var is a list, second element is the name
    if isinstance(var, list):
        name = var[1]
        var = var[0]
    else:
        name = var.name

    # Check if var is a function or a pyomo variable
    if is_regional:
        for r in m.regions:
            rows.append([name, r, unit] + [value(var[t, r]) for t in m.t])
    else:
        rows.append([name, "Global", unit] + [value(var[t]) for t in m.t])


def add_derived_global_cost_rows(rows, m, all_variables):
    """
    Add missing global cost series to the exported results.

    Some cost variables are defined only by time and region because their global
    counterparts are not needed while solving the model. To keep these variables
    available at the global level without adding equations to the optimisation
    problem, MIMOSA derives the corresponding series while exporting the results.

    A variable is aggregated when it:

    - is a Pyomo variable indexed by time and region;
    - has `fraction_of_GDP` as its unit;
    - contains `costs` in its name; and
    - does not already have a `global_<variable name>` counterpart.

    If an exported `<variable name>_abs` quantity exists, its regional values are
    used as the numerator:

    $$
    \\text{global costs}_t =
    \\frac{\\sum_r \\text{absolute costs}_{t,r}}
    {\\text{global GDP gross}_t}.
    $$

    Otherwise, absolute regional costs are reconstructed from the GDP-relative
    values:

    $$
    \\text{global costs}_t =
    \\frac{\\sum_r \\left(\\text{costs}_{t,r}
    \\cdot \\text{GDP gross}_{t,r}\\right)}
    {\\text{global GDP gross}_t}.
    $$

    The resulting `global_*` rows are added only to the exported CSV file. They
    are not added as Pyomo components and therefore cannot be accessed as
    attributes of the model. Global variables that already exist in the model are
    exported normally and are not replaced by this calculation.
    """
    variables_by_name = {
        useful_var.name: useful_var for useful_var in all_variables
    }
    existing_names = set(variables_by_name)

    for useful_var in all_variables:
        source_var = getattr(useful_var.var, "_var", useful_var.var)
        global_name = f"global_{useful_var.name}"

        if (
            getattr(source_var, "ctype", None) is not Var
            or useful_var.indices != ["t", "regions"]
            or str(useful_var.unit) != "fraction_of_GDP"
            or "costs" not in useful_var.name
            or global_name in existing_names
        ):
            continue

        absolute_costs = variables_by_name.get(f"{useful_var.name}_abs")
        global_values = []
        for t in m.t:
            if absolute_costs is not None:
                numerator = sum(
                    value(absolute_costs.var[t, r]) for r in m.regions
                )
            else:
                numerator = sum(
                    value(useful_var.var[t, r]) * value(m.GDP_gross[t, r])
                    for r in m.regions
                )
            global_values.append(numerator / value(m.global_GDP_gross[t]))

        rows.append(
            [global_name, "Global", useful_var.unit, *global_values]
        )


def rows_to_dataframe(rows, m):
    years = ["{:g}".format(year) for year in m.year(np.array(m.t))]
    columns = ["Variable", "Region", "Unit"] + years
    return pd.DataFrame(rows, columns=columns)


# def add_param_columns(dataframe, params, exp_id, experiment):
#     values = {
#         "carbonbudget": params["emissions"]["carbonbudget"],
#         "minlevel": params["emissions"]["global min level"],
#         "inertia": params["emissions"]["inertia"]["regional"],
#         "gamma": params["economics"]["MAC"]["gamma"],
#         "PRTP": params["economics"]["PRTP"],
#         "damage_coeff": first(params["regions"])["damages"][
#             "a2"
#         ],  # NOTE, only for global run
#         "perc_reversible": params["economics"]["damages"]["percentage reversible"],
#         "TCRE": params["temperature"]["TCRE"],
#     }
#     for i, (name, val) in enumerate(values.items()):
#         dataframe.insert(i + 2, name, val)

#     # Add ID:
#     dataframe.insert(0, "ID", exp_id)
#     if experiment is not None:
#         dataframe.insert(1, "Experiment", experiment)
