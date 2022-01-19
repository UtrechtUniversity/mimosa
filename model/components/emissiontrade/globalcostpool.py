"""
Model equations and constraints:
Emission trading module
Type: global cost pool
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    Constraint,
    NonNegativeReals,
    quant,
    value,
)

from model.components.abatement import AC


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emission trading equations and constraints
    (global cost pool specification)

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

    m.area_under_MAC = Var(
        m.t,
        m.regions,
        within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.area_under_MAC[t, r]
                == AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r],
                "abatement_costs",
            ),
        ]
    )

    # How are mitigation costs distributed over regions?
    m.min_rel_payment_level = Param()
    m.max_rel_payment_level = Param()
    m.extra_paid_abatement = Var(
        m.t,
        m.regions,
        initialize=0.0,
        within=NonNegativeReals,
        units=quant.unit("currency_unit"),
    )
    m.extra_received_abatement = Var(
        m.t,
        m.regions,
        initialize=0.0,
        within=NonNegativeReals,
        units=quant.unit("currency_unit"),
    )
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.extra_paid_abatement[t, r]
                <= (m.max_rel_payment_level - 1)
                * m.area_under_MAC[t, r]  # TODO change " - 1"
                if value(m.max_rel_payment_level) is not False
                else Constraint.Skip
            ),
            RegionalConstraint(
                lambda m, t, r: m.extra_received_abatement[t, r]
                <= (1 - m.min_rel_payment_level)
                * m.area_under_MAC[t, r]  # TODO change "1 - "
                if value(m.min_rel_payment_level) is not False
                else Constraint.Skip
            ),
            RegionalConstraint(
                lambda m, t, r: m.abatement_costs[t, r]
                == m.area_under_MAC[t, r]
                + m.extra_paid_abatement[t, r]
                - m.extra_received_abatement[t, r],
                "abatement_is_real_costs_plus_extra_paid_minus_extra_received",
            ),
            GlobalConstraint(
                lambda m, t: sum(m.extra_paid_abatement[t, r] for r in m.regions)
                == sum(m.extra_received_abatement[t, r] for r in m.regions),
                "total_extra_abatement_paid_equals_total_extra_abatement_received",
            ),
        ]
    )

    return constraints
