"""
Model equations and constraints:
Avoided damages and GDP loss compared to a no-policy baseline.
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    value,
    quant,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Uses the simulation results of the no-policy baseline to calculate the avoided damages
    and GDP loss compared to a no-policy baseline.
    """
    constraints = []

    m.nopolicy_damage_costs = Param(
        m.t,
        m.regions,
        mutable=True,
        units=quant.unit("fraction_of_GDP"),
    )
    m.avoided_damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.avoided_damage_costs_global = Var(m.t, units=quant.unit("fraction_of_GDP"))

    constraints.extend(
        [
            RegionalEquation(
                m.avoided_damage_costs,
                lambda m, t, r: m.nopolicy_damage_costs[t, r] - m.damage_costs[t, r],
            ),
            GlobalEquation(
                m.avoided_damage_costs_global,
                lambda m, t: (
                    sum(
                        m.avoided_damage_costs[t, r] * m.GDP_gross[t, r]
                        for r in m.regions
                    )
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    return constraints
