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
    constraints.extend(coacch._get_constraints_temperature_dependent(m))

    # Get constraints for sea-level rise damages
    constraints.extend(_get_constraints_slr(m))

    return constraints


def _get_constraints_slr(m):
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

    m.slr_gross_damage_a = Param(m.regions, doc="regional::ACCREU.slr_gross_damage_a")
    m.slr_gross_damage_b = Param(m.regions, doc="regional::ACCREU.slr_gross_damage_b")

    constraints.append(
        RegionalEquation(
            m.damage_costs_slr,
            lambda m, t, r: (
                m.damage_scale_factor
                * damage_fct_slr(
                    m.total_SLR[t],
                    m.total_SLR[0],
                    m.slr_gross_damage_a[r],
                    m.slr_gross_damage_b[r],
                )
            ),
        )
    )

    return constraints


def damage_fct_slr(slr, initial_slr, coeff_a, coeff_b):
    """
    Function to calculate the damages due to sea-level rise (SLR).

    The damage function is quadratic, defined by:
        a * slr + b * slr^2
    (or linear when b is zero).

    To make sure that the damages are zero in 2020, the damage at initial SLR
    is subtracted from the total damage:

        damage = (a * slr + b * slr^2) - (a * initial_slr + b * initial_slr^2)
    """
    if coeff_b == 0:
        damages = coeff_a * slr
        initial_damages = coeff_a * initial_slr
    else:
        damages = coeff_a * slr + coeff_b * slr**2
        initial_damages = coeff_a * initial_slr + coeff_b * initial_slr**2

    return damages - initial_damages
