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


from .. import coacch
from . import sealevelrise
from . import riverine_flooding
from . import labour_productivity


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    ACCREU damage specification

    Currently, the temperature-dependent damages are taken directly from the COACCH
    specification.

    """
    constraints = []

    # # Get constraints for temperature dependent damages
    # constraints.extend(coacch.get_constraints_temperature_dependent(m))

    # Get constraints for sea-level rise damages
    constraints.extend(sealevelrise.get_constraints(m))

    # Get constraints for riverine flooding damages
    constraints.extend(riverine_flooding.get_constraints(m))

    # Get constraints for labour productivity damages
    constraints.extend(labour_productivity.get_constraints(m))

    # Add all non-SLR sectors together

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_costs_non_slr = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_costs_abs = Var(m.t, m.regions, units=quant.unit("currency_unit"))
    m.damage_scale_factor = Param(doc="::economics.damages.scale factor")
    m.damage_relative_global = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
    )
    # Total damages are sum of non-SLR and SLR damages
    constraints.extend(
        [
            RegionalEquation(
                m.damage_costs_non_slr,
                lambda m, t, r: m.damage_costs_labourprod[t, r]
                + m.damage_costs_riverine[t, r],
            ),
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

    return constraints
