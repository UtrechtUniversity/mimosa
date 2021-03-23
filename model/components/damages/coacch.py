"""
Model equations and constraints:
Damage and adaptation costs, RICE specification
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
)

from .ad_rice2012 import get_slr_constraints


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Damage and adaptation costs equations and constraints
    (COACCH specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs multiplied by gross GDP)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    # Sea level rise
    constraints.extend(get_slr_constraints(m))

    m.damage_costs = Var(m.t, m.regions)
    m.damage_scale_factor = Param()

    # Damages not related to SLR (dependent on temperature)
    m.resid_damages = Var(m.t, m.regions)

    m.damage_noslr_b1 = Param(m.regions)
    m.damage_noslr_b2 = Param(m.regions)
    m.damage_noslr_a = Param(m.regions)

    # Quadratic damage function for non-SLR damages. Factor `a` represents
    # the damage quantile
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.resid_damages[t, r]
            == damage_fct(m.temperature[t], m.T0, m, r),
            "resid_damages",
        )
    )

    # SLR damages
    m.SLR_damages = Var(m.t, m.regions)

    m.damage_slr_b1 = Param(m.regions)
    m.damage_slr_a = Param(m.regions)

    # Linear damage function for SLR damages, including adaptation costs
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.SLR_damages[t, r]
            == m.damage_slr_a[r] * (m.damage_slr_b1[r] / 100) * m.total_SLR[t],
            "SLR_damages",
        )
    )

    # Total damages are sum of non-SLR and SLR damages
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.damage_costs[t, r]
            == m.resid_damages[t, r] + m.SLR_damages[t, r],
            "damage_costs",
        ),
    )

    return constraints


#################
## Utils
#################


# Damage function


def damage_fct(temperature, init_temp, m, r):

    # TODO COACCH damage functions are as function of 1980-2005 temperature, not PI
    quadr_fct = (
        lambda temp: m.damage_noslr_a[r]
        * (m.damage_noslr_b1[r] * temp + m.damage_noslr_b2[r] * temp ** 2)
        / 100
    )

    damage = quadr_fct(temperature)
    if init_temp is not None:
        damage -= quadr_fct(init_temp)

    return damage
