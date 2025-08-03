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
                * damage_fct_slr(
                    m.total_SLR[t],
                    m.total_SLR[0],
                    m.slr_gross_damage_a[r],
                    m.slr_gross_damage_b[r],
                    m.slr_gross_damage_c[r],
                )
            ),
        )
    )

    ##################
    ### Step 2: adaptation level and functions for avoided damages and adaptation costs
    ##################

    # Both the avoided damage function and the adaptation cost function are defined
    # as a function of the adaptation level. When the adaptation level is 0,
    # there is no adaptation, and when it is 1, the adaptation is optimal.

    # Note that while there are bounds here for the adaptation level between 0 and 1,
    # it could be higher than 1 by removing those bounds, which means that the adaptation
    # is more than optimal.

    m.slr_adaptation_level = Var(m.t, m.regions, bounds=(0, 1))

    ### Step 2a: avoided damage function

    # The avoided damages are a linear function of the adaptation level:
    # 0 when adaptation level is 0, and the optimal avoided damages when adaptation
    # level is 1:
    #
    #   p_{avoided_damages,opt}(SLR) * adapt_level
    #
    # The parameter p_{avoided_damages,opt}(SLR) is dependent on the SLR, and given
    # the variable `slr_optimal_adapt_avoided_damages`. It is a linear function
    # of SLR:
    #
    #   p_{avoided_damages,opt}(SLR) = slr_optimal_adapt_avoided_damages_param_a * SLR

    m.slr_optimal_adapt_avoided_damages = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    # Function for avoided damages: a * SLR
    m.slr_optimal_adapt_avoided_damages_param_a = Param(
        m.regions, doc="regional::ACCREU.slr_optimal_adapt_avoided_damages_a"
    )

    constraints.append(
        # Equation to determine how much damages are avoided if adaptation were optimal
        # These functions only determine the y-value of the function for level = 1.
        RegionalEquation(
            m.slr_optimal_adapt_avoided_damages,
            lambda m, t, r: (
                m.slr_optimal_adapt_avoided_damages_param_a[r] * m.total_SLR[t]
            ),
        )
    )

    ### Step 2b: adaptation costs function

    # The adaptation costs are a quadratic function of the adaptation level:
    #
    #   p_{adapt_costs,opt}(SLR) * adapt_level^2
    #
    # The parameter p_{adapt_costs,opt}(SLR) is dependent on the SLR, and given
    # the variable `slr_optimal_adapt_costs`. It is a linear function
    # of SLR:
    #
    #   p_{adapt_costs,opt}(SLR) = slr_optimal_adapt_costs_param_a + slr_optimal_adapt_costs_param_b * SLR

    m.slr_optimal_adapt_costs = Var(m.t, m.regions, units=quant.unit("currency_unit"))

    # Function for adaptation costs: a + b * SLR
    m.slr_optimal_adapt_costs_param_a = Param(
        m.regions, doc="regional::ACCREU.slr_optimal_adapt_costs_a"
    )
    m.slr_optimal_adapt_costs_param_b = Param(
        m.regions, doc="regional::ACCREU.slr_optimal_adapt_costs_b"
    )

    constraints.append(
        # Equation to determine the adaptation costs for optimal adaptation
        RegionalEquation(
            m.slr_optimal_adapt_costs,
            lambda m, t, r: (
                (
                    m.slr_optimal_adapt_costs_param_a[r]
                    + m.slr_optimal_adapt_costs_param_b[r] * m.total_SLR[t]
                )
                * m.population[t, r]
                / m.global_population[t]
                ## NOTE! In this dummy implementation, we've taken the global adaptation cost function.
                ## Just giving every region these costs would lead to costs being 26 times too high.
                ## Therefore, for now, we do a population weighting.
                ## In the future, we should not use a single parameter for all regions,
                ## but rather a regional parameter.
            ),
        )
    )

    ##################
    ### Step 3: avoided damages and adaptation costs
    ##################

    # Now that we have defined the functions for the parameters in the avoided damages
    # and adaptation costs functions, we can actually calculate the avoided damages and
    # adaptation costs using:
    #    p_{avoided_damages,opt}(SLR) * adapt_level
    # and
    #    p_{adapt_costs,opt}(SLR) * adapt_level^2.

    m.slr_avoided_damages = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.slr_adaptation_costs = Var(m.t, m.regions, units=quant.unit("currency_unit"))
    m.slr_adaptation_costs_rel = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    constraints.extend(
        [
            RegionalEquation(
                m.slr_avoided_damages,
                lambda m, t, r: (
                    m.slr_optimal_adapt_avoided_damages[t, r]
                    * m.slr_adaptation_level[t, r]
                ),
            ),
            RegionalEquation(
                m.slr_adaptation_costs,
                lambda m, t, r: (
                    m.slr_optimal_adapt_costs[t, r] * m.slr_adaptation_level[t, r] ** 2
                ),
            ),
            # Extra equation to calculate adaptation costs as fraction of GDP
            RegionalEquation(
                m.slr_adaptation_costs_rel,
                lambda m, t, r: (m.slr_adaptation_costs[t, r] / m.GDP_gross[t, r]),
            ),
        ]
    )

    # Total SLR damages are the sum of gross damages minus avoided damages plus adaptation costs
    constraints.append(
        RegionalEquation(
            m.damage_costs_slr,
            lambda m, t, r: (
                m.slr_gross_damage_costs[t, r]
                - (
                    m.slr_avoided_damages[t, r] - m.slr_avoided_damages[0, r]
                )  # Normalize such that 2020 is zero
                + m.slr_adaptation_costs_rel[t, r]
            ),
        )
    )

    return constraints


def damage_fct_slr(slr, initial_slr, a, b, c):
    """
    Function to calculate the damages due to sea-level rise (SLR).

    The damage function is quadratic, defined by:
        a + b * slr + c * slr^2
    (or linear when c is zero).

    To make sure that the damages are zero in 2020, the damage at initial SLR
    is subtracted from the total damage:

        damage = (a + b * slr + c * slr^2) - (a + b * initial_slr + c * initial_slr^2)
    """
    if c == 0:
        damages = a + b * slr
        initial_damages = a + b * initial_slr
    else:
        damages = a + b * slr + c * slr**2
        initial_damages = a + b * initial_slr + c * initial_slr**2

    return damages - initial_damages
