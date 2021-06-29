"""
Model equations and constraints:
Utility and global welfare
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    GlobalConstraint,
    soft_min,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Utility and welfare equations

    Necessary variables:
        m.utility
        m.welfare

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    # Parameters
    m.elasmu = Param()

    m.utility = Var(m.t, m.regions, initialize=0.1)
    m.yearly_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.utility[t, r]
                == calc_utility(m.consumption[t, r], m.L(m.year(t), r), m.elasmu),
                "utility",
            ),
            GlobalConstraint(
                lambda m, t: m.yearly_welfare[t]
                == sum(m.L(m.year(t), r) * m.utility[t, r] for r in m.regions),
                "yearly_welfare",
            ),
        ]
    )

    return constraints


def calc_utility(consumption, population, elasmu):
    return (soft_min(consumption / population) ** (1 - elasmu) - 1) / (1 - elasmu) - 1
