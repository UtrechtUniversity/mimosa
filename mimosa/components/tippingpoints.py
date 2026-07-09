"""
Model equations and constraints:
Sea level rise (height of sea level rise, not SLR damages)
From RICE 2010
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalEquation,
    NonNegativeReals,
    quant,
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """Comments"""

    m.param1 = Param(initialize=1.0)
    m.var1 = Var(m.t, m.regions)

    constraints = []

    m.var2 = Var(m.t)

    constraints.extend(
        [GlobalEquation(m.var2, lambda m, t: sum(m.var1[t, r] for r in m.regions))]
    )

    return constraints
