from mimosa import MIMOSA, load_params
from mimosa.common import Var, Param, Set, UsefulVar, save_output, get_indices
import numpy as np

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)


class SimVar:
    def __init__(self, var):
        self._var = var
        index_set = var.index_set()
        self.index = index_set.ordered_data()
        self.indices = get_indices(var)
        self.indices_map = {
            index.name: index.ordered_data() for index in var.index_set().subsets()
        }
        self.indices_values = [
            index.ordered_data() for index in var.index_set().subsets()
        ]  # To be removed

        self.index_to_position_map = [
            {index: i for i, index in enumerate(index_values)}
            for index_values in self.indices_map.values()
        ]

        self.dims = [len(index) for index in self.indices_values]
        if isinstance(var[self.index[0]], str):
            var_type = object
        else:
            var_type = float
        self.values = np.empty(self.dims, dtype=var_type)

        # Get the values from the Pyomo Var or Param object:
        for i in self.index:
            # Most of the time, var[i] is a Var object. Get its value
            # using the .value attribute. If it is not a Var object, just
            # assign it directly. This is the case for some Param objects.
            try:
                self.values[self._position_index(i)] = var[i].value
            except AttributeError:
                self.values[self._position_index(i)] = var[i]

        self.name = var.name
        try:
            self.unit = var._units._pint_unit
        except AttributeError:
            self.unit = None

    def _index_or_slice(self, i, index):
        if isinstance(index, slice):
            return index
        return self.index_to_position_map[i][index]

    def _position_index(self, indices):
        if not isinstance(indices, tuple):
            indices = (indices,)
        if len(indices) == 1:
            return (self._index_or_slice(0, indices[0]),)
        if len(indices) == 2:
            return (
                self._index_or_slice(0, indices[0]),
                self._index_or_slice(1, indices[1]),
            )
        return tuple(self._index_or_slice(i, index) for i, index in enumerate(indices))

    def __getitem__(self, key):
        return self.values[self._position_index(key)]

    def __setitem__(self, key, value):
        self.values[self._position_index(key)] = value

    def __repr__(self):
        values_str = str(self.values)
        if len(values_str) > 50:
            values_str = values_str[:50] + "...}"
        unit_str = f" [{self.unit}]" if self.unit else ""
        return f"SimVar({self.name}, {values_str}){unit_str}"


class SimulationObjectModel:
    def __init__(self, concrete_model):
        # Recreate all variables and
        self.all_vars = []
        for var in concrete_model.component_objects([Var, Param]):
            if not var.name.startswith("_"):
                if var.index_set().dimen > 0:
                    setattr(self, var.name, SimVar(var))
                    if "t" in [x.name for x in var.index_set().subsets()]:
                        self.all_vars.append(var.name)
                else:
                    setattr(self, var.name, var.value)
        # Recreate all sets
        for index_set in concrete_model.component_objects(Set):
            if not index_set.name.startswith("_"):
                setattr(self, index_set.name, index_set.ordered_data())
        # Add custom elements
        self.year = concrete_model.year


# For saving only:
class SimulationUsefulVar(UsefulVar):
    def __init__(self, sim_m: SimulationObjectModel, name: str):
        self.m = sim_m
        self.var = getattr(sim_m, name)

        self.name = name
        self.indices = self.var.indices
        self.is_regional = len(self.indices) > 1
        self.unit = self.var.unit

        self.index_values = {
            index: list(getattr(sim_m, index)) for index in self.indices
        }


sim_m = SimulationObjectModel(model1.concrete_model)

from mimosa import all_constraints
from inspect import signature

import time

num_params_all = {
    var_name: len(signature(expr).parameters)
    for var_name, expr in all_constraints.expressions_rhs.items()
}


def simulate(sim_m, show_time=False):

    if show_time:
        t1 = time.time()

    for t in sim_m.t:
        for var_name, expr in all_constraints.expressions_rhs.items():
            # Check if it is a regional or global constraint using len(signature(expr_rhs).parameters)
            num_params = num_params_all[var_name]
            if num_params == 3:  # Regional:
                try:
                    r = slice(None)
                    value = expr(sim_m, t, r)
                    getattr(sim_m, var_name)[t, r] = value
                except (TypeError, NotImplementedError):
                    # print(var_name, t)
                    for r in sim_m.regions:
                        value = expr(sim_m, t, r)
                        getattr(sim_m, var_name)[t, r] = value
            elif num_params == 2:  # Global:
                value = expr(sim_m, t)
                getattr(sim_m, var_name)[t] = value
            else:
                raise ValueError(
                    f"Unexpected number of parameters in expression {var_name}: {num_params}"
                )
    if show_time:
        t2 = time.time()
        print(f"Time taken to evaluate all expressions: {t2 - t1:.3f} seconds")


# Save simulation output
simulate(sim_m, show_time=True)
all_variables = [SimulationUsefulVar(sim_m, name) for name in sim_m.all_vars]
save_output(all_variables, params, sim_m, "run5_sim")


# import re
# import pandas as pd

# CONCRETE_MODEL = model1.concrete_model

# # Get all constraints:
# all_constraints = []
# for attr in dir(CONCRETE_MODEL):
#     if attr.startswith("constraint_"):
#         constraint = getattr(CONCRETE_MODEL, attr)
#         all_constraints.append(constraint)

# TIMESTEP = 2


# def extract_variables(expr_str):
#     pattern = f"([a-zA-Z_0-9]+)\\[{TIMESTEP}"
#     matches = re.findall(pattern, expr_str)
#     return matches


# def analyse_expression(constraint):
#     if not constraint.equality:
#         return {}, []
#     expr = constraint.expr
#     expr_str = str(expr)
#     lhs, rhs = expr_str.split("==")
#     lhs_vars = set(extract_variables(lhs))
#     rhs_vars = set(extract_variables(rhs))
#     # Check if expression is in the form of x == ...
#     if len(lhs_vars) != 1:
#         print(f"Not a single variable on the left side in constraint {str(constraint)}")

#     nodes = lhs_vars.union(rhs_vars)
#     links = []
#     for lhs_var in lhs_vars:
#         for rhs_var in rhs_vars:
#             links.append((rhs_var, lhs_var))
#     return nodes, links


# all_nodes = set()
# all_links = []
# timestep = 2
# for constraint in all_constraints:
#     nodes, links = {}, []
#     try:
#         nodes, links = analyse_expression(constraint[TIMESTEP])
#     except (AttributeError, KeyError) as e:
#         pass
#     try:
#         nodes, links = analyse_expression(constraint[TIMESTEP, "WEU"])
#     except (AttributeError, KeyError) as e:
#         pass
#     all_nodes.update(nodes)
#     all_links += links


# # For each node, check if it's a variable or a param
# def node_type(node):
#     if isinstance(getattr(CONCRETE_MODEL, node), Param):
#         return "Input parameter"
#     elif isinstance(getattr(CONCRETE_MODEL, node), Var):
#         return "Variable"
#     else:
#         return "Unknown"


# all_nodes = [{"Name": node, "Type": node_type(node)} for node in all_nodes]

# pd.DataFrame(all_nodes).to_csv("mimosa_nodes.csv", index=False)
# pd.DataFrame(all_links).to_csv("mimosa_links.csv", index=False)

model1.solve()
model1.save("run5_pyomo")
