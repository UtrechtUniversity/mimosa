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

def soft_relu(x, a=10.0):
    return 1/a * log(1+exp(a*x))

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



####### Get all variables of a model

class UsefulVar:
    def __init__(self, m, name: str):
        self.m = m
        var = getattr(m, name)
        
        self.name = name
        self.is_regional, self.indices = self._get_indices(var)

        self.index_values = {
            index: list(getattr(m, index))
            for index in self.indices
        }

    # Private functions
    def _get_indices(self, var):
        # Check if variable has multiple indices:
        if var._implicit_subsets is None:
            # Variable has a single index
            return False, [var.index_set().name]
        else:
            # Variable has multiple indices
            return True, [index.name for index in var._implicit_subsets]

def get_all_variables(m):
    return [
        UsefulVar(m, var.name)
        for var in m.component_objects(Var)
        if not var.name.startswith('_')
    ]