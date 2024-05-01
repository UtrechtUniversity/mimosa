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
    """
    Without emission trading, the import/export of emission reductions and mitigation costs is always zero:

    $$
    \\text{import/export mitigation cost balance}_{t,r} = 0
    $$

    This means that the mitigation costs and the area under the MAC are exactly the same for each region (see [Mitigation costs](mitigation.md#mitigation-costs)).
    """
    constraints = []  # No constraints here

    m.import_export_emission_reduction_balance = Param(
        m.t, m.regions, units=quant.unit("emissionsrate_unit"), initialize=0
    )
    m.import_export_mitigation_cost_balance = Param(
        m.t, m.regions, units=quant.unit("currency_unit"), initialize=0
    )

    return constraints
