"""
Model equations and constraints:
Damage and adaptation costs
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    GeneralConstraint,
    RegionalEquation,
    Param,
    quant,
)


def get_constraints(
    m: AbstractModel, options: dict = None
) -> Sequence[GeneralConstraint]:
    """Damage and adaptation costs equations and constraints
    (no-damage specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs, as % of GDP)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.damage_costs = Var(m.t, m.regions, initialize=0.0)
    m.non_market_damage_costs_abs = Param(
        m.t, m.regions, initialize=0.0, units=quant.unit("currency_unit")
    )
    constraints.extend([RegionalEquation(m.damage_costs, lambda m, t, r: 0.0)])

    return constraints
