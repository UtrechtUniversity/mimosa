import numpy as np

from mimosa.common import get_indices, Var, Param, Set, UsefulVar


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
            type_var = object
        else:
            type_var = float
        self.values = np.empty(self.dims, dtype=type_var)

        # Get the values from the Pyomo Var or Param object:
        for i in self.index:
            # Most of the time, var[i] is a Var object. Get its value
            # using the .value attribute. If it is not a Var object, just
            # assign it directly. This is the case for some Param objects.
            try:
                self.set_indexed(i, var[i].value)
            except AttributeError:
                # If var[i] is not a Var object, it might be a Param or Set
                self.set_indexed(i, var[i])

        self.name = var.name
        try:
            self.unit = var._units._pint_unit
        except AttributeError:
            self.unit = None

    def _position_index(self, key):
        """
        Convert external Pyomo-style index values to internal NumPy positions.

        Examples:
            "CAN" -> 0
            (2020, "CAN") -> (0, 0)
        """
        if isinstance(key, tuple):
            if len(key) == 2:
                # Often, we have two indices: time and region. In that case, we can use a faster lookup.
                return (
                    self.index_to_position_map[0][key[0]],
                    self.index_to_position_map[1][key[1]],
                )
            return tuple(self.index_to_position_map[i][k] for i, k in enumerate(key))
        return self.index_to_position_map[0][key]

    def __getitem__(self, key):
        return self.values[self._position_index(key)]

    def __setitem__(self, key, value):
        self.values[self._position_index(key)] = value

    def get_positional(self, key):
        """Returns the value given the index position (e.g. 0 instead of 'USA')."""
        return self.values[key]

    def get_indexed(self, index):
        """Returns the value given the index value, not index position (e.g. 'USA' instead of 0)."""
        return self.values[self._position_index(index)]

    def get_all_indexed(self):
        """Returns all values as a dictionary with index values as keys."""
        return {index: self.get_indexed(index) for index in self.index}

    def set_indexed(self, index, value):
        """Sets the value given the index value, not index position (e.g. 'USA' instead of 0)."""
        self.values[self._position_index(index)] = value

    def set_positional(self, key, value):
        """Sets the value given the index position (e.g. 0 instead of 'USA')."""
        self.values[key] = value

    def __repr__(self):
        values_str = str(self.values)
        if len(values_str) > 50:
            values_str = values_str[:50] + "...}"
        unit_str = f" [{self.unit}]" if self.unit else ""
        return f"SimVar({self.name}, {values_str}){unit_str}"

    def copy(self):
        """Returns a copy of the SimVar object."""
        new_var = SimVar(self._var)
        new_var.values = np.copy(self.values)
        return new_var


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
        self.index_sets = []
        for index_set in concrete_model.component_objects(Set):
            if not index_set.name.startswith("_"):
                self.index_sets.append(index_set.name)
                index_set_names = index_set.ordered_data()
                setattr(self, index_set.name, index_set_names)

        # Add custom elements
        self.year = concrete_model.year

    def all_vars_for_export(self):
        return [SimulationUsefulVar(self, name) for name in self.all_vars]


class SimulationUsefulVar(UsefulVar):
    def __init__(self, sim_m: SimulationObjectModel, name: str):
        self.m = sim_m
        self.var = getattr(
            sim_m, name
        ).copy()  # Use copy to avoid modifying the original SimVar
        self.var.use_indexed = True

        self.name = name
        self.indices = self.var.indices
        self.is_regional = len(self.indices) > 1
        self.unit = self.var.unit

        self.index_values = {
            index: list(getattr(sim_m, index)) for index in self.indices
        }
