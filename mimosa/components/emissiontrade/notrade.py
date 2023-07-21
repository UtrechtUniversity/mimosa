"""
Model equations and constraints:
Emission trading module
Type: no trade
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, RegionalConstraint, Param

from mimosa.components.abatement import AC


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emission trading equations and constraints
    (no-trade specification)

    Necessary variables:
        m.abatement_costs (abatement costs as paid for by this region)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.import_export_emission_reduction_balance = Param(m.t, m.regions, initialize=0)

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: (m.abatement_costs[t, r])
                == AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r],
                "abatement_costs",
            ),
        ]
    )

    return constraints
