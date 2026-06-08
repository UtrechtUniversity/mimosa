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
    NonNegativeReals,
)


def get_constraints(m):
    """
    Defines the equations for the gross damages, residual damages, and
    adaptation costs due to sea-level rise (SLR).
    """
    constraints = []

    # SLR damages
    m.damage_costs_slr = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    m.slr_gross_damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    # m.slr_gross_damage_a = Param(m.regions, doc="regional::ACCREU.slr_gross_dmg_a_p50")
    m.slr_gross_damage_b1 = Param(m.regions, doc="regional::ACCREU_sectoral.SLR_linear")
    m.slr_gross_damage_b2 = Param(
        m.regions, doc="regional::ACCREU_sectoral.SLR_quadratic"
    )

    m.slr_adapt_effectiveness_limit = Param(
        doc="::economics.adaptation.slr_effectiveness_limit"
    )

    ##################
    ### Step 1: gross damages
    ##################

    # Define the gross damages as a function of SLR:
    #
    #       a * (b1 * SLR + b2 * SLR^2) - (a * (b1 * initial_SLR + b2 * initial_SLR^2))
    # If b2 is zero, the function is linear:
    #       a * (b1 * SLR) - (a * (b1 * initial_SLR))

    # SLR damages are as function of SLR relative to 1995-2014. TODO: fix this better.
    temp_fix_slr_1995_2014 = 0.08

    constraints.append(
        RegionalEquation(
            m.slr_gross_damage_costs,
            lambda m, t, r: (
                m.damage_scale_factor
                * (
                    damage_fct_slr(
                        m.total_SLR[t] - m.total_SLR[0],
                        1,
                        m.slr_gross_damage_b1[r],
                        m.slr_gross_damage_b2[r],
                    )
                    - damage_fct_slr(
                        0,
                        1,
                        m.slr_gross_damage_b1[r],
                        m.slr_gross_damage_b2[r],
                    )
                )
            ),
        )
    )

    ##################
    ### Step 2: Avoided damages
    ##################

    m.slr_avoided_damages = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.slr_adaptation_costs_rel = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    constraints.append(RegionalEquation(m.slr_avoided_damages, avoided_damages_eq))

    ##################
    ### Step 3: residual damages and adaptation costs
    ##################

    # Total SLR damages are the sum of gross damages minus avoided damages plus adaptation costs
    constraints.append(
        RegionalEquation(
            m.damage_costs_slr,
            lambda m, t, r: (
                m.slr_gross_damage_costs[t, r]
                * (1 - m.slr_avoided_damages[t, r])  # Residual damages after adaptation
                + m.slr_adaptation_costs_rel[t, r]
            ),
        )
    )

    return constraints


def damage_fct_slr(slr, a, b1, b2):
    """
    Function to calculate the damages due to sea-level rise (SLR).

    The damage function is quadratic, defined by:
        a * (b1 * slr + b2 * slr^2)
    (or linear when b2 is zero).

    """
    if b2 == 0:
        return a * (b1 * slr) / 100.0

    return a * (b1 * slr + b2 * slr**2) / 100.0


def avoided_damages_eq(m, t, r):
    """
    Adaptation effectiveness function for sea-level rise (SLR) damages, based on the fitted function in ACCREU:
    Avoided damages = L * (1 - exp(-beta * adaptation_costs))
    """
    # These parameters should be made regional
    L = m.slr_adapt_effectiveness_limit
    beta = 0.304093

    # The fitted function had absolute adaptation costs as x-axis for its global function. To apply
    # it regionally, we switch to relative adaptation costs by multiplying the x-axis with the world GDP
    # This is temporary and should be replaced when we have regional functions.
    factor = 120_000

    return L * (1 - exp(-beta * m.slr_adaptation_costs_rel[t, r] * factor))
