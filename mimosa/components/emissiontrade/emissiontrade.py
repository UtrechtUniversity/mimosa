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
    RegionalSoftEqualityConstraint,
    value,
    soft_min,
)

from mimosa.components.abatement import AC


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

    m.global_carbonprice = Var(m.t)
    m.impose_global_carbon_price = Param()

    # The global mitigation cost pool:
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.area_under_MAC[t, r]
                == AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r],
                "abatement_costs",
            ),
            # Constraint that sets the global carbon price to the average of the regional carbon prices:
            GlobalConstraint(
                lambda m, t: m.global_carbonprice[t]
                == sum(
                    m.carbonprice[t, r] * m.population(m.year(t), r) for r in m.regions
                )
                / sum(m.population(m.year(t), r) for r in m.regions),
                "global_carbonprice",
            ),
            RegionalSoftEqualityConstraint(
                lambda m, t, r: m.carbonprice[t, r],
                lambda m, t, r: m.global_carbonprice[t],
                "carbonprice_equals_global_carbonprice",
                epsilon=0.1,
                ignore_if=lambda m, t, r: m.year(t) <= 2020
                or not value(m.impose_global_carbon_price),
            ),
        ]
    )

    ## Extra reporting variables:

    m.paid_for_emission_reductions = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.import_export_emission_reduction_balance = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.import_export_mitigation_cost_balance = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: sum(m.abatement_costs[t, r] for r in m.regions)
                == sum(m.area_under_MAC[t, r] for r in m.regions),
                "sum_abatement_equals_sum_area_under_mac",
            ),
            RegionalConstraint(
                lambda m, t, r: m.abatement_costs[t, r]
                == m.area_under_MAC[t, r]
                + m.import_export_mitigation_cost_balance[t, r]
                if t > 0
                else Constraint.Skip,
                "abatement_costs_equals_area_under_mac_plus_import_export_mitigation_cost_balance",
            ),
            # Constraint: from import/export mitigation costs to import/export of emissions using the global carbon price
            RegionalConstraint(
                lambda m, t, r: m.import_export_emission_reduction_balance[t, r]
                == m.import_export_mitigation_cost_balance[t, r]
                / soft_min(m.global_carbonprice[t])
                if t > 0
                else Constraint.Skip,
                "import_export_emission_reduction_balance",
            ),
            # Constraint: paid for emission reductions
            RegionalConstraint(
                lambda m, t, r: m.paid_for_emission_reductions[t, r]
                == (
                    m.regional_emission_reduction[t, r]
                    + m.import_export_emission_reduction_balance[t, r]
                )
                if t > 0
                else Constraint.Skip,
                "paid_for_emission_reductions",
            ),
        ]
    )

    return constraints
