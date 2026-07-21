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
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    In MIMOSA, every region can physically reduce its own emissions. The domestic cost is determined
    by the area under the MAC (see [Mitigation](mitigation.md#mitigation-costs)). Emission trading
    allows the reductions and mitigation costs attributed to a region to differ from the reductions
    and costs occurring within that region.

    The associated financial flow is captured by
    $\\text{mitigation cost trading balance}_{t,r}$. A positive balance increases the mitigation costs
    attributed to a region; a negative balance reduces them. For every timestep,
    the sum of these transfers should be zero:

    $$
    \\sum_r \\text{mitigation cost trading balance}_{t,r} = 0
    $$

    A single global carbon price is used to convert the financial flow
    (`mitigation_cost_trading_balance`) into a flow of attributed emission reductions
    (`emission_reduction_trading_balance`):

    $$
    \\text{emission reduction trading balance}_{t,r} = \\frac{\\text{mitigation cost trading balance}_{t,r}}{\\text{global carbon price}_{t}},
    $$

    where the global carbon price is the population weighted average of the regional carbon prices:

    $$
    \\text{global carbon price}_{t} = \\frac{\\sum_r \\text{carbon price}_{t,r} \\cdot \\text{population}_{t,r}}{\\sum_r \\text{population}_{t,r}}.
    $$

    The emission reductions attributed to a region are calculated as the physical reductions in that region plus its
    emission reduction trading balance:

    $$
    \\text{attributed emission reductions}_{t,r} = \\text{regional emission reduction}_{t,r} + \\text{emission reduction trading balance}_{t,r}.
    $$

    Regional emission allowances are the baseline emissions minus the reductions attributed to the region:

    $$
    \\text{regional emission allowances}_{t,r} = \\text{baseline emissions}_{t,r} - \\text{attributed emission reductions}_{t,r}.
    $$

    """
    constraints = []

    m.global_carbon_price = Var(m.t)

    # Emissions are traded at the global carbon price
    constraints.extend(
        [
            # Constraint that sets the global carbon price to the average of the regional carbon prices:
            GlobalEquation(
                m.global_carbon_price,
                lambda m, t: sum(
                    m.carbon_price[t, r] * m.population[t, r] for r in m.regions
                )
                / m.global_population[t],
            ),
        ]
    )

    ## Extra reporting variables:

    m.attributed_emission_reductions = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.regional_emission_allowances = Var(
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
            GlobalConstraint(
                lambda m, t: sum(
                    m.mitigation_cost_trading_balance[t, r] for r in m.regions
                )
                == 0.0,
                "sum_mitigation_equals_sum_area_under_mac",
            ),
            # Convert the mitigation-cost trading balance into the emission-reduction trading balance
            RegionalEquation(
                m.emission_reduction_trading_balance,
                lambda m, t, r: (
                    m.mitigation_cost_trading_balance[t, r]
                    / soft_min(m.global_carbon_price[t])
                    if t > 0
                    else 0
                ),
            ),
            # Constraint: emission reductions attributed to the region after trading
            RegionalEquation(
                m.attributed_emission_reductions,
                lambda m, t, r: (
                    m.regional_emission_reduction[t, r]
                    + m.emission_reduction_trading_balance[t, r]
                    if t > 0
                    else Constraint.Skip
                ),
            ),
            # Constraint: regional emission allowances, equal to baseline minus attributed emission reductions
            RegionalEquation(
                m.regional_emission_allowances,
                lambda m, t, r: (
                    m.baseline_emissions[t, r] - m.attributed_emission_reductions[t, r]
                    if t > 0
                    else m.baseline_emissions[t, r]
                ),
            ),
        ]
    )

    return constraints
