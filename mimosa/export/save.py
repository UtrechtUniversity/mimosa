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
from mimosa.common import (
    Var,
    get_all_variables,
    get_all_time_dependent_params,
    quant,
    value,
)


def save_output_pyomo(
    params,
    m,
    filename="run1",
    hash_suffix=False,
    folder="output",
    runtime=None,
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
        runtime=runtime,
    )


def save_output(
    all_variables,
    params,
    m,
    filename,
    scenario_type="optimisation",
    hash_suffix=False,
    folder="output",
    runtime=None,
):
    # 1. Create a unique identifier
    if hash_suffix:
        settings_hash = hashlib.md5(json.dumps(params).encode()).hexdigest()[:9]
    else:
        settings_hash = ""

    rows = []
    for useful_var in all_variables:
        var_to_row(rows, m, useful_var.var, useful_var.is_regional, useful_var.unit)
    add_derived_global_rows(rows, m, all_variables)
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
        if runtime is not None:
            params_with_version["Runtime (seconds)"] = round(runtime, 2)
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


def add_derived_global_rows(rows, m, all_variables):
    """
    Add missing global series to the exported results.

    Some variables are defined only by time and region because their global
    counterparts are not needed while solving the model. To keep selected
    variables available at the global level without adding equations to the
    optimisation problem, MIMOSA derives the corresponding series while exporting
    the results.

    A variable can be aggregated when it:

    - is a Pyomo variable indexed by time and region;
    - does not already have a `global_<variable name>` counterpart.

    Regional population quantities, such as variables measured in `billion
    people`, are summed directly:

    $$
    \\text{global population quantity}_t =
    \\sum_r \\text{population quantity}_{t,r}.
    $$

    Regional cost variables are aggregated when they have `fraction_of_GDP` as
    their unit and contain `costs` in their name.

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

    Regional adaptation effectiveness variables measured as
    `fraction_of_gross_damages` are weighted by the corresponding sector's
    absolute gross damages. The corresponding gross-damage variable is inferred
    from the name: `<sector>_avoided_damages_adapt` uses
    `<sector>_damage_costs_gross`. If global gross damages are zero, the exported
    avoided fraction is `NaN`.

    The resulting `global_*` rows are added only to the exported CSV file. They
    are not added as Pyomo components and therefore cannot be accessed as
    attributes of the model. Global variables that already exist in the model are
    exported normally and are not replaced by this calculation.
    """
    variables_by_name = {useful_var.name: useful_var for useful_var in all_variables}
    existing_names = set(variables_by_name)

    people_dimensionality = quant.unit("people", pyomo=False).dimensionality

    for useful_var in all_variables:
        source_var = getattr(useful_var.var, "_var", useful_var.var)
        global_name = f"global_{useful_var.name}"

        if (
            getattr(source_var, "ctype", None) is not Var
            or useful_var.indices != ["t", "regions"]
            or global_name in existing_names
        ):
            continue

        unit_str = str(useful_var.unit) if useful_var.unit is not None else ""
        unit_dimensionality = (
            quant.unit(unit_str, pyomo=False).dimensionality if unit_str else None
        )

        if unit_dimensionality == people_dimensionality:
            global_values = [
                sum(value(useful_var.var[t, r]) for r in m.regions) for t in m.t
            ]
        elif unit_str == "fraction_of_GDP" and "costs" in useful_var.name:
            absolute_costs = variables_by_name.get(f"{useful_var.name}_abs")
            global_values = []
            for t in m.t:
                if absolute_costs is not None:
                    numerator = sum(value(absolute_costs.var[t, r]) for r in m.regions)
                else:
                    numerator = sum(
                        value(useful_var.var[t, r]) * value(m.GDP_gross[t, r])
                        for r in m.regions
                    )
                global_values.append(numerator / value(m.global_GDP_gross[t]))
        elif unit_str == "fraction_of_gross_damages":
            avoided_damages_suffix = "_avoided_damages_adapt"
            if not useful_var.name.endswith(avoided_damages_suffix):
                continue

            sector_name = useful_var.name[: -len(avoided_damages_suffix)]
            gross_damages = variables_by_name.get(
                f"{sector_name}_damage_costs_gross"
            )
            if gross_damages is None:
                continue

            global_values = []
            for t in m.t:
                gross_damages_abs = {
                    r: value(gross_damages.var[t, r])
                    * value(m.GDP_gross[t, r])
                    for r in m.regions
                }
                denominator = sum(gross_damages_abs.values())
                numerator = sum(
                    value(useful_var.var[t, r]) * gross_damages_abs[r]
                    for r in m.regions
                )
                global_values.append(
                    np.nan
                    if np.isclose(denominator, 0.0)
                    else numerator / denominator
                )
        else:
            continue

        rows.append([global_name, "Global", useful_var.unit, *global_values])


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
