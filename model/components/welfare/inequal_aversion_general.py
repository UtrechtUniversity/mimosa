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
    m.inequal_aversion = Param()

    m.utility = Var(m.t, m.regions, initialize=10)
    m.yearly_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.utility[t, r]
                == calc_regional_utility(
                    m.consumption[t, r], m.L(m.year(t), r), m.inequal_aversion
                ),
                "utility",
            ),
            GlobalConstraint(
                lambda m, t: m.yearly_welfare[t]
                == sum(m.L(m.year(t), r) for r in m.regions)
                * calc_global_utility(
                    sum(m.utility[t, r] for r in m.regions),
                    sum(m.L(m.year(t), r) for r in m.regions),
                    m.elasmu,
                    m.inequal_aversion,
                ),
                "yearly_welfare",
            ),
        ]
    )

    return constraints


def calc_regional_utility(consumption, population, inequal_aversion):
    return population * soft_min(consumption / population) ** (1 - inequal_aversion)


def calc_global_utility(
    sum_regional_utility, global_population, elasmu, inequal_aversion
):
    return soft_min(sum_regional_utility / global_population) ** (
        (1 - elasmu) / (1 - inequal_aversion)
    ) / (1 - elasmu)
