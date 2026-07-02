"""
Model equations and constraints:
Emission trading module
Type: global cost pool
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    Constraint,
    NonNegativeReals,
    quant,
)

from mimosa.components.mitigation import AC


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emission trading equations and constraints
    (global cost pool specification)

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
    constraints = []

    m.domestic_mitigation_costs = Var(
        m.t,
        m.regions,
        within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )

    # The global mitigation cost pool:
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.domestic_mitigation_costs[t, r]
                == AC(m.relative_abatement[t, r], m, t, r) * m.baseline_emissions[t, r],
                "mitigation_costs",
            ),
            GlobalConstraint(
                lambda m, t: sum(m.mitigation_costs[t, r] for r in m.regions)
                == sum(m.domestic_mitigation_costs[t, r] for r in m.regions),
                "sum_mitigation_costs_equals_sum_domestic_mitigation_costs",
            ),
        ]
    )

    ## Extra reporting variables:

    m.attributed_emission_reductions = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.emission_reduction_trading_balance = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.mitigation_cost_trading_balance = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: (
                    m.attributed_emission_reductions[t, r]
                    == m.mitigation_costs[t, r]
                    * m.global_emission_reduction_per_cost_unit[t]
                    if t > 0
                    else Constraint.Skip
                ),
                "paid_for_emission_reductions",
            ),
            # Import export of emission reduction balance: if positive: , if negative:
            RegionalConstraint(
                lambda m, t, r: (
                    m.emission_reduction_trading_balance[t, r]
                    == m.attributed_emission_reductions[t, r]
                    - m.regional_emission_reduction[t, r]
                    if t > 0
                    else Constraint.Skip
                ),
                "import_export_emission_reduction_balance",
            ),
            RegionalConstraint(
                lambda m, t, r: m.mitigation_cost_trading_balance[t, r]
                == m.mitigation_costs[t, r] - m.domestic_mitigation_costs[t, r],
                "import_export_mitigation_cost_balance",
            ),
        ]
    )

    # How are mitigation costs distributed over regions?
    m.min_rel_payment_level = Param(
        doc="::economics.emission trade.min rel payment level"
    )
    m.max_rel_payment_level = Param(
        doc="::economics.emission trade.max rel payment level"
    )

    return constraints
