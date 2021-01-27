import typing
from abc import ABC, abstractmethod

from pyomo.environ import (
    AbstractModel,
    Set, 
    TransformationFactory, SolverFactory, SolverStatus,
    Objective, Param, Var, Constraint, 
    value, maximize, 
    log, exp, tanh, sqrt,
    NonNegativeReals
)

####### Extra functions
def pow(x, a, abs=False):
    if abs:
        return (x**2)**(a/2)
    else:
        return x**a

####### Constraints

class GeneralConstraint(ABC):
    
    def __init__(self, rule: typing.Callable, name: str=None):
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