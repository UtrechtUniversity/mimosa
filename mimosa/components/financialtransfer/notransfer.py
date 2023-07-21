"""
Model equations and constraints:
Financial transfer for damage costs module
Type: no transfer
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, RegionalConstraint, Param


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

    # Since it is always zero, it is better to make it a Param instead of Var for numerical stability
    m.financial_transfer = Param(m.t, m.regions, initialize=0)
    m.rel_financial_transfer = Param(m.t, m.regions, initialize=0)

    return constraints
