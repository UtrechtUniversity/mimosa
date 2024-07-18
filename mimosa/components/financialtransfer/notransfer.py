"""
Model equations and constraints:
Financial transfer for damage costs module
Type: no transfer
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, quant, Param


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Without financial transfers, this variable is always equal to zero:

    $$
    \\text{financial transf.}_{t,r} = \\text{rel. financial transf.} = 0.0
    $$
    """
    constraints = []

    # Since it is always zero, it is better to make it a Param instead of Var for numerical stability
    m.financial_transfer = Param(
        m.t, m.regions, initialize=0, units=quant.unit("currency_unit")
    )
    m.rel_financial_transfer = Param(
        m.t, m.regions, initialize=0, units=quant.unit("fraction_of_GDP")
    )

    return constraints
