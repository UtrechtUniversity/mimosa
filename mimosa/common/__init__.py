"""
Imports all common modules and extra imports
"""

# Logging
import logging

logger = logging.getLogger("MIMOSA")

# General imports
from dataclasses import dataclass

# Pyomo imports
from pyomo.environ import (
    AbstractModel,
    ConcreteModel,
    Set,
    TransformationFactory,
    SolverFactory,
    SolverStatus,
    SolverManagerFactory,
    Objective,
    Param,
    Var,
    log,
    sqrt,
    tanh,
    value,
    maximize,
    minimize,
    NonNegativeReals,
    Any,
    units as u,
)
from pyomo.opt.base.solvers import OptSolver

# Pyomo utils
from .pyomo_utils import (
    Constraint,  # Only for Constraint.Skip
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    GlobalSoftEqualityConstraint,
    RegionalSoftEqualityConstraint,
    Equation,
    GlobalEquation,
    RegionalEquation,
    UsefulVar,
    soft_switch,
    soft_min,
    soft_max,
    get_all_variables,
    get_all_time_dependent_params,
    add_constraint,
    has_time_and_region_dim,
    get_indices,
    atan,
    exp,
)

# Other utils
from .utils import first

from .units import quant

from ..export import save_output, save_output_pyomo

# # Datastore
# from .data import DataStore

# # Config
# from .config import params

# Compatibility imports
import numpy as np

try:
    trapezoid = np.trapezoid
except AttributeError:
    trapezoid = np.trapz  # For compatibility with older numpy versions
