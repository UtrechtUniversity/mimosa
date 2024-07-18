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
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    When allowing financial transfers for a global damage cost pool, a region can
    receive financial transfers up to its level of climate damages:

    $$
    \\text{financial transf.}_{t,r} \\geq - \\text{damages}_{t,r} \\cdot \\text{GDP}_{\\text{gross},t,r}
    $$

    The sum of financial transfers per time period should be zero, since it is a redistribution
    of costs:

    $$
    \\sum_r \\text{financial transf.}_{t,r} = 0
    $$

    Also, in the first year, no financial transfers are allowed:

    $$ \\text{financial_transf.}_{0,r} = 0. $$

    Finally, the financial transfers are expressed in currency units (dollars). They can also
    be expressed as percentage of GDP:

    $$
    \\text{rel. financial transf.}_{t,r} = \\frac{\\text{financial transf.}_{t,r}}{\\text{GDP}_{\\text{gross},t,r}}
    $$


    """
    constraints = []

    # Note: positive financial transfer means paying money, negative means receiving
    m.financial_transfer = Var(
        m.t, m.regions, initialize=0, units=quant.unit("currency_unit")
    )
    m.rel_financial_transfer = Var(
        m.t, m.regions, initialize=0, units=quant.unit("fraction_of_GDP")
    )

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    sum(m.financial_transfer[t, r] for r in m.regions) == 0.0
                    if t > 0
                    else Constraint.Skip
                ),
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
