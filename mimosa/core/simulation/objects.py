import numpy as np

from mimosa.common import get_indices, Var, Param, Set, UsefulVar


class SimVar:
    def __init__(self, var, default_use_indexed=False):

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

        self.use_indexed = default_use_indexed

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

    def _index_or_slice(self, i, index):
        """
        If index is a slice, return it. Otherwise, return the position in the index.
        This way, you can access a value using x['USA'] for one element, or x[:] for all items
        """
        if isinstance(index, slice):
            return index
        return self.index_to_position_map[i][index]

    def _position_index(self, indices):
        """
        Converts indices (like 'USA') to position in the index (like 0).
        If the index is a slice, it returns the slice as is.
        """
        if not isinstance(indices, tuple):
            indices = (indices,)
        return tuple(self._index_or_slice(i, index) for i, index in enumerate(indices))

    def __getitem__(self, key):
        if self.use_indexed:
            # If use_indexed is True, we use the indexed method
            return self.get_indexed(key)
        return self.values[key]

    def __setitem__(self, key, value):
        if self.use_indexed:
            # If use_indexed is True, we use the indexed method
            self.set_indexed(key, value)
            return
        self.values[key] = value

    def get_indexed(self, index):
        """Returns the value given the index value, not index position (e.g. 'USA' instead of 0)."""
        return self.values[self._position_index(index)]

    def get_all_indexed(self):
        """Returns all values as a dictionary with index values as keys."""
        return {index: self.get_indexed(index) for index in self.index}

    def set_indexed(self, index, value):
        """Sets the value given the index value, not index position (e.g. 'USA' instead of 0)."""
        self.values[self._position_index(index)] = value

    def __repr__(self):
        values_str = str(self.values)
        if len(values_str) > 50:
            values_str = values_str[:50] + "...}"
        unit_str = f" [{self.unit}]" if self.unit else ""
        return f"SimVar({self.name}, {values_str}){unit_str}"

    def copy(self):
        """Returns a copy of the SimVar object."""
        new_var = SimVar(self._var, self.use_indexed)
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
                index_set_numpy_index = list(range(len(index_set_names)))
                setattr(self, index_set.name + "_names", index_set_names)
                setattr(self, index_set.name + "_numpy_index", index_set_numpy_index)
        # By default, use numpy indices as sets:
        self.set_index_numpy_index()
        # Add custom elements
        self.year = concrete_model.year

    def set_index_numpy_index(self):
        """
        Sets the index sets (m.t, m.regions, ...) to numpy indices (0, 1, 2...)
        """
        for index_set in self.index_sets:
            setattr(self, index_set, getattr(self, index_set + "_numpy_index"))

    def set_index_names(self):
        """
        Sets the index sets (m.t, m.regions, ...) to their original names ('CAN', 'USA', ...)
        """
        for index_set in self.index_sets:
            setattr(self, index_set, getattr(self, index_set + "_names"))

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
