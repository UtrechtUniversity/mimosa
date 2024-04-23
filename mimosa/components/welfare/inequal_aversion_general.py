"""
Model equations and constraints:
Utility and global welfare
"""

from typing import Sequence

from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    GlobalConstraint,
    soft_min,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    <h3>General inequality aversion</h3>

    TODO

    <h3>Parameters defined in this module</h3>
    - param::elasmu
    - param::inequal_aversion

    """
    constraints = []

    # Parameters
    m.elasmu = Param(doc="::economics.elasmu")
    m.inequal_aversion = Param(doc="::economics.inequal_aversion")

    m.utility = Var(m.t, m.regions, initialize=10)
    m.yearly_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.utility[t, r]
                == calc_regional_utility(
                    m.consumption[t, r], m.population[t, r], m.inequal_aversion
                ),
                "utility",
            ),
            GlobalConstraint(
                lambda m, t: m.yearly_welfare[t]
                == sum(m.population[t, r] for r in m.regions)
                * calc_global_utility(
                    sum(m.utility[t, r] for r in m.regions),
                    sum(m.population[t, r] for r in m.regions),
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
