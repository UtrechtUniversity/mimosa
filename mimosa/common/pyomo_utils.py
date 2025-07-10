import typing
import re
from abc import ABC, abstractmethod
import numpy as np
from pyomo.core.base.units_container import PintUnitExtractionVisitor

from pyomo.environ import Var, Constraint, Param
import pyomo.environ

# Monkey patch to make sure that the unit stays the same after calling a arctan-function.
# By default, the unit becomes "radian", causing trouble in subsequent unit comparisons.
# Since we use arctan a lot as a "soft-min/max" function, the unit should stay the same as
# the input unit
PintUnitExtractionVisitor.unary_function_method_map["atan"] = (
    PintUnitExtractionVisitor._get_unit_for_single_child
)


from pyomo.environ import units


def atan(x):
    name = type(x).__name__
    if name in ["Series", "DataFrame", "float", "int", "ndarray"]:
        return np.arctan(x)

    return pyomo.environ.atan(x)


def exp(x):
    name = type(x).__name__
    if name in ["Series", "DataFrame", "float", "int", "ndarray"]:
        return np.exp(x)

    return pyomo.environ.exp(x)


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
    return atan(a * x) / np.pi + 0.5


def soft_min(x, scale=1.0):
    """Soft minimum: approximates the function f(x)=x for x > 0 and f(x)=0 for x <= 0

    Args:
        x
        scale (float, optional): order of magnitude of expected values. Defaults to 1.0.

    Returns:
        approximately x if x > 0 and 0 if x <= 0
    """
    a = scale_to_a(scale)
    soft_min_value = soft_switch(x, scale) * x + 1 / (a * np.pi)
    return soft_min_value

    # Make sure the final answer is positive. Increases computing time, but reduces errors.
    # return sqrt(
    #     soft_min_value ** 2
    # )


def soft_max(x, maxval, scale=1.0):
    return -soft_min(maxval - x, scale) + maxval


####### Equations


class Equation(ABC):

    lhs: str
    rhs: typing.Callable
    name: str
    dependencies: typing.List[str] = []

    # Soft dependencies are dependencies to the previous time step, which should
    # not affect order of execution, but are important to plot
    prev_time_dependencies: typing.List[str] = []

    def __init__(self, lhs, rhs, indices=None):
        """
        Represents an equation of the form lhs == rhs. Note that the lhs
        can only be a single variable, while the rhs can be a function.

        Use GlobalEquation for time dependent equations (e.g. global emissions) and
        RegionalEquation for regional equations (e.g. regional emissions).

        Args:
            lhs (Union[str, Var]): The left-hand side variable name given as string or
                as a Pyomo Var object.
            rhs (Callable): A function that takes m and the indices (e.g. m, t or m, t, r) as
                arguments and returns the right-hand side value.
            indices (list, optional): List of indices for the equation. Defaults to ['t', 'r'].

        Example:
            GlobalEquation(
                lhs="temperature",
                rhs=lambda m, t: m.T0 + m.TCRE * m.cumulative_emissions[t]
            )

            which will be evaluated as:
            m.temperature[t] == m.T0 + m.TCRE * m.cumulative_emissions[t]

            or:

            RegionalEquation(
                lhs=m.regional_emissions,
                rhs=lambda m, t, r: (1 - m.relative_abatement[t, r]) * m.baseline[t, r]
            )

            which will be evaluated as:
            m.regional_emissions[t, r] == (1 - m.relative_abatement[t, r]) * m.baseline[t, r]

        """

        indices = indices or ["t", "r"]  # Default indices are time and region]

        if isinstance(lhs, Var):
            lhs = lhs.name

        self.lhs = lhs
        self.rhs = rhs

        self.name = lhs

    def __call__(self, m, *indices):
        """
        Evaluates the right-hand side of the equation with the given indices.

        Example:
            eq = GlobalEquation(lhs="temperature", rhs=lambda m, t: m.T0 + m.TCRE * m.cumulative_emissions[t])
            eq(m, t)
        """
        value = self.rhs(m, *indices)
        if ".Skip" in str(value):
            return 0
        return value

    @abstractmethod
    def to_pyomo_constraint(self, m):
        pass


class GlobalEquation(Equation):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs, indices=["t", "r"])

    __init__.__doc__ = Equation.__init__.__doc__

    def to_pyomo_constraint(self, m):
        """
        Converts the equation to a Pyomo constraint.
        """

        def _rule(m, t, lhs_var_name=self.lhs, rhs_expr=self.rhs):
            rhs_value = rhs_expr(m, t)
            if ".Skip" in str(rhs_value):
                return Constraint.Skip
            return getattr(m, lhs_var_name)[t] == rhs_value

        return Constraint(m.t, rule=_rule)


class RegionalEquation(Equation):
    def __init__(self, lhs, rhs):
        super().__init__(lhs, rhs, indices=["t", "r"])

    __init__.__doc__ = Equation.__init__.__doc__

    def to_pyomo_constraint(self, m):
        """
        Converts the equation to a Pyomo constraint.
        """

        def _rule(m, t, r, lhs_var_name=self.lhs, rhs_expr=self.rhs):
            rhs_value = rhs_expr(m, t, r)
            if ".Skip" in str(rhs_value):
                return Constraint.Skip
            return getattr(m, lhs_var_name)[t, r] == rhs_value

        return Constraint(m.t, m.regions, rule=_rule)


####### Constraints


class GeneralConstraint(ABC):
    def __init__(self, rule: typing.Callable, name: str = None, doc: str = None):
        """Adds a constraint to the Pyomo mimosa.

        Args:
            rule (typing.Callable): function with parameters m, [t], [r]
            name (str, optional): name of the constraint, useful for debugging. Defaults to None.
            doc (str, optional): documentation of the constraint. Defaults to None.
        """

        self.name = name
        self.rule = rule
        self.doc = doc

    @abstractmethod
    def to_pyomo_constraint(self, m):
        pass


class GlobalConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(m.t, rule=self.rule, doc=self.doc)


class GlobalInitConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(rule=self.rule, doc=self.doc)


class RegionalConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(m.t, m.regions, rule=self.rule, doc=self.doc)


class RegionalInitConstraint(GeneralConstraint):
    def to_pyomo_constraint(self, m):
        return Constraint(m.regions, rule=self.rule, doc=self.doc)


class GeneralSoftEqualityConstraint(GeneralConstraint):
    def __init__(
        self,
        rule_lhs: typing.Callable,
        rule_rhs: typing.Callable,
        name: str = None,
        epsilon: float = 0.005,
        absolute_epsilon: float = None,
        ignore_if: typing.Callable = None,
    ):
        """Creates a constraint of the type:
            rule_lhs(x) <= (1 + eps) * rule_rhs(x) && rule_lhs(x) >= (1 - eps) * rule_rhs(x)
        Useful for creating "soft-equality" constraints

        Args:
            rule_lhs (typing.Callable): function (left-hand side) with parameters m, [t], [r]
            rule_rhs (typing.Callable): function (right-hand side) with parameters m, [t], [r]
            name (str, optional): name of the constraint, useful for debugging. Defaults to None.
            epsilon (float, optional): tolerance for upper/lower bounds. Defaults to 0.005.
            ignore_if (typing.Callable): function with parameters m that returns True when constraint should be ignored
        """
        super().__init__(rule_lhs, [f"{name}_upperbound", f"{name}_lowerbound"])

        self.rule_rhs = rule_rhs
        self.epsilon = epsilon
        self.absolute_epsilon = absolute_epsilon

        if ignore_if is None:
            ignore_if = (
                lambda m, *args, **kwargs: False
            )  # Never ignore when ignore_if is None
        self.ignore_if = ignore_if

    def rhs_eps(self, rule_rhs, is_upper: bool, *args):
        factor = 1 if is_upper else -1
        if self.absolute_epsilon is not None:
            return rule_rhs(*args) + factor * self.absolute_epsilon
        return (1 + factor * self.epsilon) * rule_rhs(*args)


class GlobalSoftEqualityConstraint(GeneralSoftEqualityConstraint):
    def to_pyomo_constraint(self, m):
        eps = self.epsilon
        rule_lhs = self.rule
        rule_rhs = self.rule_rhs

        upperbound = lambda m, t: (
            rule_lhs(m, t) <= self.rhs_eps(rule_rhs, True, m, t)
            if not self.ignore_if(m, t)
            else Constraint.Skip
        )
        lowerbound = lambda m, t: (
            rule_lhs(m, t) >= self.rhs_eps(rule_rhs, False, m, t)
            if not self.ignore_if(m, t)
            else Constraint.Skip
        )
        return [
            Constraint(m.t, rule=upperbound),
            Constraint(m.t, rule=lowerbound),
        ]


class RegionalSoftEqualityConstraint(GeneralSoftEqualityConstraint):
    def to_pyomo_constraint(self, m):
        eps = self.epsilon
        rule_lhs = self.rule
        rule_rhs = self.rule_rhs

        upperbound = lambda m, t, r: (
            rule_lhs(m, t, r) <= self.rhs_eps(rule_rhs, True, m, t, r)
            if not self.ignore_if(m, t, r)
            else Constraint.Skip
        )
        lowerbound = lambda m, t, r: (
            rule_lhs(m, t, r) >= self.rhs_eps(rule_rhs, False, m, t, r)
            if not self.ignore_if(m, t, r)
            else Constraint.Skip
        )
        return [
            Constraint(m.t, m.regions, rule=upperbound),
            Constraint(m.t, m.regions, rule=lowerbound),
        ]


def add_constraint(m, constraints, names=None):
    """Adds a constraint to the model

    It first generates a unique name, then adds
    the constraint using this new name
    """
    if not isinstance(constraints, list):
        constraints = [constraints]
        names = [names]

    name = None
    for constraint, name in zip(constraints, names):
        n = len(list(m.component_objects()))
        name = f"constraint_{n}" if name is None else f"constraint_{name}"
        m.add_component(name, constraint)
    return name


####### Get all variables of a model


class UsefulVar:
    def __init__(self, m, var: typing.Union[Var, Param]):
        self.m = m
        self.var = var

        self.name = var.name
        self.unit = get_unit(self.var)
        self.indices = get_indices(self.var)
        self.is_regional = len(self.indices) > 1

        self.index_values = {index: list(getattr(m, index)) for index in self.indices}


def get_all_variables(m):
    return [
        UsefulVar(m, var)
        for var in m.component_objects(Var)
        if not var.name.startswith("_")
    ]


def get_all_time_dependent_params(m):
    """Returns all parameters with time and region dimensions"""
    return [
        UsefulVar(m, param)
        for param in m.component_objects(Param)
        if "t" in get_indices(param) and not param.name.startswith("_")
    ]


def has_time_and_region_dim(var):
    """Returns true if the Pyomo variable `var` is regional, false if it is global"""
    # While there is no explicit Pyomo way to obtain the indices, we can use
    # this private property to check if variable has multiple indices
    return var.index_set().dimen > 1


def get_indices(var):
    return [index.name for index in var.index_set().subsets()]


def get_unit(var):
    pyomo_unit = units.get_units(var)
    pyomo_unit_str = str(pyomo_unit) if pyomo_unit is not None else ""

    # Bugfix replace "/a" to "/yr" ("annum" is less clear than year)
    # Note that we should not replace e.g. "/atm", hence the negative lookahead
    return re.sub("/a(?![a-zA-Z])", "/yr", pyomo_unit_str)
