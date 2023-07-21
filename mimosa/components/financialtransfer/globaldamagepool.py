"""
Model equations and constraints:
Financial transfer for damage costs module
Type: global damage cost pool
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    GeneralConstraint,
    RegionalConstraint,
    GlobalConstraint,
    RegionalInitConstraint,
    Constraint,
    Var,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Damage cost trading equations and constraints
    (no-trade specification)

    Necessary variables:
        - m.financial_transfer

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    # Note: positive financial transfer means paying money, negative means receiving
    m.financial_transfer = Var(m.t, m.regions, initialize=0)
    m.rel_financial_transfer = Var(m.t, m.regions, initialize=0)

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: sum(m.financial_transfer[t, r] for r in m.regions) == 0.0
                if t > 0
                else Constraint.Skip,
                "zero_sum_of_yearly_financial_transfer",
            ),
            RegionalInitConstraint(
                lambda m, r: m.financial_transfer[0, r] == 0.0,
                "no_transfer_in_first_year",
            ),
            RegionalConstraint(
                lambda m, t, r: m.financial_transfer[t, r]
                >= -m.damage_costs[t, r] * m.GDP_gross[t, r],
                "received_financial_transfer_max_own_damages",
            ),
            RegionalConstraint(
                lambda m, t, r: m.rel_financial_transfer[t, r] * m.GDP_gross[t, r]
                == m.financial_transfer[t, r],
                "financial_transfer_rel_to_gdp",
            ),
        ]
    )

    return constraints
