from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    GlobalConstraint,
    GlobalEquation,
    RegionalEquation,
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
    their emissions, or receive payments for reducing their own emissions.

    The financial transfers for
    this are captured in the variable $\\text{import/export mitigation cost balance}_{t,r}$. For every timestep,
    the sum of these transfers should be zero:

    $$
    \\sum_r \\text{import/export mitigation cost balance}_{t,r} = 0
    $$

    All emissions are traded at the global carbon price. Therefore, the financial flows (mitigation cost balance) is
    translated into emission flows (import/export emission reduction balance) using the global carbon price:

    $$
    \\text{import/export emission reduction balance}_{t,r} = \\frac{\\text{import/export mitigation cost balance}_{t,r}}{\\text{global carbon price}_{t}},
    $$

    where the global carbon price is the population weighted average of the regional carbon prices:

    $$
    \\text{global carbon price}_{t} = \\frac{\\sum_r \\text{carbon price}_{t,r} \\cdot \\text{population}_{t,r}}{\\sum_r \\text{population}_{t,r}}.
    $$

    Finally, the emission reductions paid for by a region are calculated as the physical reductions in the region plus the
    import/export emission reduction balance:

    $$
    \\text{paid for emission reductions}_{t,r} = \\text{regional emission reduction}_{t,r} + \\text{import/export emission reduction balance}_{t,r}.
    $$



    """
    constraints = []

    m.global_carbonprice = Var(m.t)

    # Emissions are traded at the global carbon price
    constraints.extend(
        [
            # Constraint that sets the global carbon price to the average of the regional carbon prices:
            GlobalEquation(
                m.global_carbonprice,
                lambda m, t: sum(
                    m.carbonprice[t, r] * m.population[t, r] for r in m.regions
                )
                / m.global_population[t],
            ),
        ]
    )

    ## Extra reporting variables:

    m.paid_for_emission_reductions = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.regional_emission_allowances = Var(
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
            RegionalEquation(
                m.import_export_emission_reduction_balance,
                lambda m, t, r: (
                    m.import_export_mitigation_cost_balance[t, r]
                    / soft_min(m.global_carbonprice[t])
                    if t > 0
                    else 0
                ),
            ),
            # Constraint: paid for emission reductions
            RegionalEquation(
                m.paid_for_emission_reductions,
                lambda m, t, r: (
                    m.regional_emission_reduction[t, r]
                    + m.import_export_emission_reduction_balance[t, r]
                    if t > 0
                    else Constraint.Skip
                ),
            ),
            # Constraint: regional emission allowances, equal to baseline minus paid for emission reductions
            RegionalEquation(
                m.regional_emission_allowances,
                lambda m, t, r: (
                    m.baseline[t, r] - m.paid_for_emission_reductions[t, r]
                    if t > 0
                    else m.baseline[t, r]
                ),
            ),
        ]
    )

    return constraints
