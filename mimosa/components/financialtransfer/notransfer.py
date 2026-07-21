"""
Model equations and constraints:
Financial transfer for damage costs module
Type: no transfer
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, quant, Param, ModelContext


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    Without financial transfers, this variable is always equal to zero:

    $$
    \\text{financial transfer abs}_{t,r} = \\text{financial transfer}_{t,r} = 0.0
    $$
    """
    constraints = []

    # Since it is always zero, it is better to make it a Param instead of Var for numerical stability
    m.financial_transfer_abs = Param(
        m.t, m.regions, initialize=0, units=quant.unit("currency_unit")
    )
    m.financial_transfer = Param(
        m.t, m.regions, initialize=0, units=quant.unit("fraction_of_GDP")
    )

    return constraints
