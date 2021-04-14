import typing
from abc import ABC, abstractmethod
from numpy import pi

from pyomo.environ import Var, Constraint, atan

####### Extra functions


def scale_to_a(scale):
    return 25.0 / scale


def soft_switch(x, scale=1.0):
    """Approximates 0 for x <= 0 and 1 for x > 0

    Args:
        x
        scale (float, optional): order of magnitude of expected values. Defaults to 1.0.
    """
    a = scale_to_a(scale)
    return atan(a * x) / pi + 0.5


def soft_min(x, scale=1.0):
    """Soft minimum: approximates the function f(x)=x for x > 0 and f(x)=0 for x <= 0

    Args:
        x
        scale (float, optional): order of magnitude of expected values. Defaults to 1.0.

    Returns:
        approximately x if x > 0 and 0 if x <= 0
    """
    a = scale_to_a(scale)
    soft_min_value = soft_switch(x, scale) * x + 1 / (a * pi)
    return soft_min_value

    # Make sure the final answer is positive. Increases computing time, but reduces errors.
    # return sqrt(
    #     soft_min_value ** 2
    # )


def soft_max(x, maxval, scale=1.0):
    return -soft_min(maxval - x, scale) + maxval


####### Constraints


class GeneralConstraint(ABC):
    def __init__(self, rule: typing.Callable, name: str = None):
        """Adds a constraint to the Pyomo model.

        Args:
            rule (typing.Callable): function with parameters m, [t], [r]
            name (str, optional): name of the constraint, useful for debugging. Defaults to None.
        """

        self.name = name
        self.rule = rule

    @abstractmethod
    def to_pyomo_constraint(self, m):
        pass


class GlobalConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(m.t, rule=self.rule)


class GlobalInitConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(rule=self.rule)


class RegionalConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(m.t, m.regions, rule=self.rule)


class RegionalInitConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(m.regions, rule=self.rule)


def add_constraint(m, constraint, name=None):
    """Adds a constraint to the model

    It first generates a unique name, then adds
    the constraint using this new name
    """
    n = len(list(m.component_objects()))
    name = f"constraint_{n}" if name is None else f"constraint_{name}"
    m.add_component(name, constraint)
    return name


####### Get all variables of a model


class UsefulVar:
    def __init__(self, m, name: str):
        self.m = m
        self.var = getattr(m, name)

        self.name = name
        self.is_regional = is_regional(self.var)
        self.indices = get_indices(self.var)

        self.index_values = {index: list(getattr(m, index)) for index in self.indices}


def get_all_variables(m):
    return [
        UsefulVar(m, var.name)
        for var in m.component_objects(Var)
        if not var.name.startswith("_")
    ]


def is_regional(var):
    """Returns true if the Pyomo variable `var` is regional, false if it is global"""
    # While there is no explicit Pyomo way to obtain the indices, we can use
    # this private property to check if variable has multiple indices
    if var._implicit_subsets is None:
        return False
    return True


def get_indices(var):
    if is_regional(var):
        return [index.name for index in var._implicit_subsets]
    return [var.index_set().name]
