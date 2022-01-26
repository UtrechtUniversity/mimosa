"""
Model equations and constraints:
Burden sharing
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    RegionalSoftEqualityConstraint,
    NonNegativeReals,
    Any,
    quant,
    value,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emissions and temperature equations and constraints

    Necessary variables:

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.burden_sharing_regime = Param(within=Any)

    ## Burden sharing scheme:
    m.burden_sharing_common_cost_level = Var(
        m.t, within=NonNegativeReals, units=quant.unit("fraction_of_GDP")
    )
    constraints.extend(
        [
            # Total costs: abatement + damage costs should be equal among regions as % GDP
            RegionalSoftEqualityConstraint(
                lambda m, t, r: m.rel_abatement_costs[t, r] + m.damage_costs[t, r],
                lambda m, t, r: m.burden_sharing_common_cost_level[t],
                "burden_sharing_regime_total_costs",
                ignore_if=lambda m, t, r: value(m.burden_sharing_regime)
                != "equal_total_costs"
                or m.year(t) > 2100,
            ),
            # Abatement costs: abatement costs should be equal among regions as % GDP
            RegionalSoftEqualityConstraint(
                lambda m, t, r: m.rel_abatement_costs[t, r],
                lambda m, t, r: m.burden_sharing_common_cost_level[t],
                "burden_sharing_regime_abatement_costs",
                ignore_if=lambda m, t, r: value(m.burden_sharing_regime)
                != "equal_abatement_costs"
                or m.year(t) > 2100,
            ),
        ]
    )

    return constraints
