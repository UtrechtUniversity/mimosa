"""
Model equations and constraints:
Avoided damages and GDP loss compared to a no-policy baseline.
"""

from typing import Sequence
from mimosa.common import (
    ConcreteModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    value,
    quant,
)


def get_constraints(m: ConcreteModel) -> Sequence[GeneralConstraint]:
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
    m.avoided_damage_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
        doc="Avoided damages, calculated as the difference between the damage costs in a no-policy baseline run and the damage costs in this run.",
    )
    m.global_avoided_damage_costs = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
        doc="Global aggregation of avoided damages",
    )
    m.nopolicy_market_and_non_market_damage_costs = Param(
        m.t,
        m.regions,
        mutable=True,
        units=quant.unit("fraction_of_GDP"),
    )
    m.avoided_market_and_non_market_damage_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
        doc="Avoided market and monetised non-market damages, calculated as the no-policy damage fraction minus the policy damage fraction, each relative to its own gross GDP.",
    )
    m.global_avoided_market_and_non_market_damage_costs = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
        doc="Global aggregation of avoided market and monetised non-market damage fractions, weighted by policy gross GDP.",
    )

    constraints.extend(
        [
            RegionalEquation(
                m.avoided_damage_costs,
                lambda m, t, r: m.nopolicy_damage_costs[t, r] - m.damage_costs[t, r],
            ),
            GlobalEquation(
                m.global_avoided_damage_costs,
                lambda m, t: (
                    sum(
                        m.avoided_damage_costs[t, r] * m.GDP_gross[t, r]
                        for r in m.regions
                    )
                    / m.global_GDP_gross[t]
                ),
            ),
            RegionalEquation(
                m.avoided_market_and_non_market_damage_costs,
                lambda m, t, r: m.nopolicy_market_and_non_market_damage_costs[t, r]
                - (
                    m.damage_costs[t, r]
                    + m.non_market_damage_costs_abs[t, r] / m.GDP_gross[t, r]
                ),
            ),
            GlobalEquation(
                m.global_avoided_market_and_non_market_damage_costs,
                lambda m, t: (
                    sum(
                        m.avoided_market_and_non_market_damage_costs[t, r]
                        * m.GDP_gross[t, r]
                        for r in m.regions
                    )
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    return constraints
