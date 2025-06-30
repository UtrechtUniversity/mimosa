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
from mimosa.common import get_all_variables, get_all_time_dependent_params, value


def save_output_pyomo(params, m, filename="run1", hash_suffix=False, folder="output"):
    # 2. Save the Pyomo variables and data functions
    all_variables = get_all_variables(m) + get_all_time_dependent_params(m)
    save_output(all_variables, params, m, filename, "optimisation", hash_suffix, folder)


def save_output(
    all_variables,
    params,
    m,
    filename,
    scenario_type="optimisation",
    hash_suffix=False,
    folder="output",
):
    # 1. Create a unique identifier
    if hash_suffix:
        settings_hash = hashlib.md5(json.dumps(params).encode()).hexdigest()[:9]
    else:
        settings_hash = ""

    rows = []
    for useful_var in all_variables:
        var_to_row(rows, m, useful_var.var, useful_var.is_regional, useful_var.unit)
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
