"""
Model equations and constraints:
Damage and adaptation costs
"""

from typing import Sequence
from mimosa.common import AbstractModel, Var, GeneralConstraint, RegionalEquation


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
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
    constraints.extend([RegionalEquation(m.damage_costs, lambda m, t, r: 0.0)])

    return constraints
