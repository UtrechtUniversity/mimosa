"""
Model equations and constraints:
Emission trading module
Type: no trade
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    GeneralConstraint,
    Param,
    quant,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emission trading equations and constraints
    (no-trade specification)

    Necessary variables:
        m.mitigation_costs (abatement costs as paid for by this region)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []  # No constraints here

    m.import_export_emission_reduction_balance = Param(
        m.t, m.regions, units=quant.unit("emissionsrate_unit"), initialize=0
    )
    m.import_export_mitigation_cost_balance = Param(
        m.t, m.regions, units=quant.unit("currency_unit"), initialize=0
    )

    return constraints
