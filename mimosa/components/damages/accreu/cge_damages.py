"""
Model equations and constraints:
Damage and adaptation costs, COACCH specification
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
    soft_max,
    Any,
    exp,
    quant,
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """ """
    constraints = []

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_costs_abs = Var(m.t, m.regions, units=quant.unit("currency_unit"))
    m.damage_scale_factor = Param(doc="::economics.damages.scale factor")
    m.non_market_damage_costs_abs = Param(
        m.t, m.regions, initialize=0.0, units=quant.unit("currency_unit")
    )
    m.damage_relative_global = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
    )
    # Total damages are sum of non-SLR and SLR damages
    constraints.extend(
        [
            RegionalEquation(
                m.damage_costs,
                lambda m, t, r: m.damage_costs_non_slr[t, r] + m.damage_costs_slr[t, r],
            ),
            RegionalEquation(
                m.damage_costs_abs,
                lambda m, t, r: m.damage_costs[t, r] * m.GDP_gross[t, r],
            ),
            GlobalEquation(
                m.damage_relative_global,
                lambda m, t: (
                    sum(m.damage_costs_abs[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    # Get constraints for temperature dependent damages
    constraints.extend(get_constraints_temperature_dependent(m))

    # Get constraints for sea-level rise damages
    constraints.extend(get_constraints_slr(m))

    return constraints


def get_constraints_temperature_dependent(
    m: AbstractModel,
) -> Sequence[GeneralConstraint]:
    """ """
    constraints = []

    # Damages not related to SLR (dependent on temperature)
    m.damage_costs_non_slr = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    m.damage_noslr_b1 = Param(m.regions, doc="regional::ACCREU_CGE.NoSLR_b1")
    m.damage_noslr_b2 = Param(m.regions, doc="regional::ACCREU_CGE.NoSLR_b2")

    m.damage_noslr_a = Param(
        m.regions,
        doc=lambda params: f'regional::ACCREU_CGE.NoSLR_a{params["economics"]["damages"]["quantile"]:.2f}',
    )

    # Quadratic damage function for non-SLR damages. Factor `a` represents
    # the damage quantile
    m.temperature_1995_2014 = Param(initialize=0.85, units=quant.unit("degC_above_PI"))
    constraints.append(
        RegionalEquation(
            m.damage_costs_non_slr,
            lambda m, t, r: (
                m.damage_scale_factor
                * damage_fct(
                    m.temperature[t] - m.temperature_1995_2014,
                    m.T0 - m.temperature_1995_2014,
                    m,
                    r,
                    is_slr=False,
                )
            ),
        )
    )

    return constraints


def get_constraints_slr(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """ """
    constraints = []

    # SLR damages
    m.damage_costs_slr = Var(
        m.t, m.regions, bounds=(-0.5, 0.7), units=quant.unit("fraction_of_GDP")
    )
    m.damage_slr_b1 = Param(m.regions, doc="regional::ACCREU_CGE.slr_b1")
    m.damage_slr_b2 = Param(m.regions, doc="regional::ACCREU_CGE.slr_b2")

    m.damage_slr_a = Param(
        m.regions,
        doc=lambda params: f'regional::ACCREU_CGE.slr_a{params["economics"]["damages"]["quantile"]:.2f}',
    )

    # Linear damage function for SLR damages, including adaptation costs
    constraints.append(
        RegionalEquation(
            m.damage_costs_slr,
            lambda m, t, r: (
                m.damage_scale_factor
                * damage_fct(m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True)
            ),
        )
    )

    return constraints


#################
## Utils
#################


# Damage function


def functional_form(x, m, r, is_slr=False):
    if is_slr:
        b1, b2 = m.damage_slr_b1[r], m.damage_slr_b2[r]
        a = m.damage_slr_a[r]
    else:
        b1, b2 = m.damage_noslr_b1[r], m.damage_noslr_b2[r]
        a = m.damage_noslr_a[r]

    return a * (b1 * x + b2 * x**2) / 100.0


def damage_fct(x, x0, m, r, is_slr):
    damage = functional_form(x, m, r, is_slr)
    if x0 is not None:
        damage -= functional_form(x0, m, r, is_slr)

    return damage
