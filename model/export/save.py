"""
Generates a CSV file with a row for each variable (`Var`)
in the ConcreteModel `m`.
"""

import json
import os
import random
import hashlib
import numpy as np
import pandas as pd

from model.common import get_all_variables, value


def save_output(params, m, experiment=None, random_id=False, folder="output"):

    # 1. Create a unique identifier
    if random_id:
        exp_id = "{:08x}".format(random.getrandbits(32))
    else:
        exp_id = hashlib.md5(json.dumps(params).encode()).hexdigest()[:9]

    # 2. Save the Pyomo variables and data functions
    all_variables = get_all_variables(m)

    all_functions = [[m.population, "population"]]

    rows = []
    for var in all_functions:
        var_to_row(rows, m, var, True)
    for useful_var in all_variables:
        var_to_row(rows, m, useful_var.var, useful_var.is_regional)
    dataframe = rows_to_dataframe(rows, m)

    # add_param_columns(df, params, id, experiment)

    # 3. Save the CSV file
    os.makedirs(folder + "/", exist_ok=True)
    filename = f"{exp_id}" if experiment is None else f"{experiment}_{exp_id}"

    dataframe.to_csv(f"{folder}/{filename}.csv", float_format="%.6g", index=False)

    # 3. Save the param file
    with open(f"{folder}/{filename}.csv.params.json", "w") as fh:
        json.dump(params, fh)


def var_to_row(rows, m, var, is_regional):
    # If var is a list, second element is the name
    if isinstance(var, list):
        name = var[1]
        var = var[0]
    else:
        name = var.name

    # Check if var is a function or a pyomo variable
    if is_regional:
        fct = lambda t, r: (var(m.year(t), r) if callable(var) else value(var[t, r]))
        for r in m.regions:
            rows.append([name, r] + [fct(t, r) for t in m.t])
    else:
        fct = lambda t: (var(m.year(t)) if callable(var) else value(var[t]))
        rows.append([name, "Global"] + [fct(t) for t in m.t])


def rows_to_dataframe(rows, m):
    years = ["{:g}".format(year) for year in m.year(np.array(m.t))]
    columns = ["Variable", "Region"] + years
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
