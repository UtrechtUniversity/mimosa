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
    quant,
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    When allowing financial transfers for a global damage cost pool, a region can
    receive financial transfers up to its level of climate damages:

    $$
    \\text{financial transfer abs}_{t,r} \\geq - \\text{damage costs}_{t,r} \\cdot \\text{GDP}_{\\text{gross},t,r}
    $$

    The sum of financial transfers per time period should be zero, since it is a redistribution
    of costs:

    $$
    \\sum_r \\text{financial transfer abs}_{t,r} = 0
    $$

    Also, in the first year, no financial transfers are allowed:

    $$ \\text{financial transfer abs}_{0,r} = 0. $$

    `financial_transfer_abs` is expressed in currency units (dollars), while
    `financial_transfer` is expressed as a fraction of gross GDP:

    $$
    \\text{financial transfer}_{t,r} = \\frac{\\text{financial transfer abs}_{t,r}}{\\text{GDP}_{\\text{gross},t,r}}
    $$


    """
    constraints = []

    # Note: positive financial transfer means paying money, negative means receiving
    m.financial_transfer_abs = Var(
        m.t, m.regions, initialize=0, units=quant.unit("currency_unit")
    )
    m.financial_transfer = Var(
        m.t, m.regions, initialize=0, units=quant.unit("fraction_of_GDP")
    )

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    sum(m.financial_transfer_abs[t, r] for r in m.regions) == 0.0
                    if t > 0
                    else Constraint.Skip
                ),
                "zero_sum_of_yearly_financial_transfer",
            ),
            RegionalInitConstraint(
                lambda m, r: m.financial_transfer_abs[0, r] == 0.0,
                "no_transfer_in_first_year",
            ),
            RegionalConstraint(
                lambda m, t, r: m.financial_transfer_abs[t, r]
                >= -m.damage_costs[t, r] * m.GDP_gross[t, r],
                "received_financial_transfer_max_own_damages",
            ),
            RegionalConstraint(
                lambda m, t, r: m.financial_transfer[t, r] * m.GDP_gross[t, r]
                == m.financial_transfer_abs[t, r],
                "financial_transfer_rel_to_gdp",
            ),
        ]
    )

    return constraints
