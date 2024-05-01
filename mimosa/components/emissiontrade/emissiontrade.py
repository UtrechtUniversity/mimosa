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


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    In MIMOSA, every region can reduce its own emissions. The price for this is determined
    by the area under the MAC (see [Mitigation](mitigation.md#mitigation-costs)). On top of that,
    regions can trade emission reductions with each other. Regions can pay other regions to reduce
    their emissions, or receive payments for reducing their own emissions. The financial transfers for
    this are captured in the variable $\\text{import/export mitigation cost balance}_{t,r}$. For every timestep,
    the sum of these transfers should be zero:

    $$
    \\sum_r \\text{import/export mitigation cost balance}_{t,r} = 0
    $$



    """
    constraints = []

    m.global_carbonprice = Var(m.t)

    # Emissions are traded at the global carbon price
    constraints.extend(
        [
            # Constraint that sets the global carbon price to the average of the regional carbon prices:
            GlobalConstraint(
                lambda m, t: m.global_carbonprice[t]
                == sum(m.carbonprice[t, r] * m.population[t, r] for r in m.regions)
                / sum(m.population[t, r] for r in m.regions),
                "global_carbonprice",
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
                lambda m, t: sum(
                    m.import_export_mitigation_cost_balance[t, r] for r in m.regions
                )
                == 0.0,
                "sum_mitigation_equals_sum_area_under_mac",
            ),
            # Constraint: from import/export mitigation costs to import/export of emissions using the global carbon price
            RegionalConstraint(
                lambda m, t, r: (
                    m.import_export_emission_reduction_balance[t, r]
                    == m.import_export_mitigation_cost_balance[t, r]
                    / soft_min(m.global_carbonprice[t])
                    if t > 0
                    else Constraint.Skip
                ),
                "import_export_emission_reduction_balance",
            ),
            # Constraint: paid for emission reductions
            RegionalConstraint(
                lambda m, t, r: (
                    m.paid_for_emission_reductions[t, r]
                    == (
                        m.regional_emission_reduction[t, r]
                        + m.import_export_emission_reduction_balance[t, r]
                    )
                    if t > 0
                    else Constraint.Skip
                ),
                "paid_for_emission_reductions",
            ),
        ]
    )

    return constraints
