"""
Model equations and constraints:
Damage and adaptation costs
"""

from model.common.pyomo import Var, RegionalConstraint


def get_constraints(m):
    """Damage and adaptation costs equations and constraints
    (no-damage specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs, as % of GDP)

    Returns:
        list of constraints (GlobalConstraint, GlobalInitConstraint, RegionalConstraint, RegionalInitConstraint)
    """
    constraints = []

    m.damage_costs = Var(m.t, m.regions, initialize=0.0)
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.damage_costs[t, r] == 0.0, "zero_damage_costs"
            )
        ]
    )

    return constraints
