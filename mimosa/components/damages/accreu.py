"""
Model equations and constraints:
Damage and adaptation costs, ACCREU specification
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
    NonNegativeReals,
)

from . import coacch


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    ACCREU damage specification

    Currently, the temperature-dependent damages are taken directly from the COACCH
    specification.

    """
    constraints = []

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_scale_factor = Param(doc="::economics.damages.scale factor")
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
            GlobalEquation(
                m.damage_relative_global,
                lambda m, t: (
                    sum(m.damage_costs[t, r] * m.GDP_gross[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    # Get constraints for temperature dependent damages
    constraints.extend(coacch.get_constraints_temperature_dependent(m))

    # Get constraints for sea-level rise damages
    constraints.extend(get_constraints_slr(m))

    return constraints


def get_constraints_slr(m):
    """
    Defines the equations for the gross damages, residual damages, and
    adaptation costs due to sea-level rise (SLR).
    """
    constraints = []

    # SLR damages
    m.damage_costs_slr = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    # Get the coefficients for the SLR damage function from the CSV input file
    # (inputdata/regionalparams/ACCREU.csv).
    # Usage:
    #   m.param_name = Param(m.regions, doc="regional::ACCREU.{COLUMN_NAME_IN_CSV}")
    # Then, you can get its value using
    #   lambda m, t, r: m.param_name[r] * ... ...

    m.slr_gross_damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    m.slr_gross_damage_a = Param(m.regions, doc="regional::ACCREU.slr_gross_damage_a")
    m.slr_gross_damage_b = Param(m.regions, doc="regional::ACCREU.slr_gross_damage_b")
    m.slr_gross_damage_c = Param(m.regions, doc="regional::ACCREU.slr_gross_damage_c")

    ##################
    ### Step 1: gross damages
    ##################

    # Define the gross damages as a function of SLR:
    #
    #       a + b * SLR + c * SLR^2 - (a + b * initial_SLR + c * initial_SLR^2)
    # If c is zero, the function is linear:
    #       a + b * SLR - (a + b * initial_SLR)
    constraints.append(
        RegionalEquation(
            m.slr_gross_damage_costs,
            lambda m, t, r: (
                m.damage_scale_factor
                * (
                    damage_fct_slr(
                        m.total_SLR[t],
                        m.slr_gross_damage_a[r],
                        m.slr_gross_damage_b[r],
                        m.slr_gross_damage_c[r],
                    )
                    - damage_fct_slr(
                        m.total_SLR[0],
                        m.slr_gross_damage_a[r],
                        m.slr_gross_damage_b[r],
                        m.slr_gross_damage_c[r],
                    )
                )
            ),
        )
    )

    ##################
    ### Step 2: Avoided damages
    ##################

    m.slr_avoided_damages = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP"), bounds=(0, 1)
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


def damage_fct_slr(slr, a, b, c):
    """
    Function to calculate the damages due to sea-level rise (SLR).

    The damage function is quadratic, defined by:
        a + b * slr + c * slr^2
    (or linear when c is zero).

    """
    if c == 0:
        return a + b * slr

    return a + b * slr + c * slr**2


def avoided_damages_eq(m, t, r):
    """
    Adaptation effectiveness function for sea-level rise (SLR) damages, based on the fitted function in ACCREU:
    Avoided damages = L * (1 - exp(-beta * adaptation_costs))
    """
    # These parameters should be made regional
    L = 0.879
    beta = 0.304093

    # The fitted function had absolute adaptation costs as x-axis for its global function. To apply
    # it regionally, we switch to relative adaptation costs by multiplying the x-axis with the world GDP
    # This is temporary and should be replaced when we have regional functions.
    factor = 120_000

    return L * (1 - exp(-beta * m.slr_adaptation_costs_rel[t, r] * factor))
