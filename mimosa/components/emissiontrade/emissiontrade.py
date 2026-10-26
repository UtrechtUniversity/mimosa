from typing import Sequence
from mimosa.common import (
    ConcreteModel,
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

from mimosa.core.model_inputs import ModelInputs


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""
    In MIMOSA, every region can physically reduce its own emissions. The domestic cost is determined
    by the area under the MAC (see [Mitigation](mitigation.md#mitigation-costs)). Emission trading
    allows the reductions and mitigation costs attributed to a region to differ from the reductions
    and costs occurring within that region.

    The associated financial flow is captured by
    $\href{./#var__mitigation_cost_trading_balance}{\text{mitigation cost trading balance}_{t,r}}$. A positive balance increases the mitigation costs
    attributed to a region; a negative balance reduces them. For every timestep,
    the sum of these transfers should be zero:

    $$
    \sum_r \href{./#var__mitigation_cost_trading_balance}{\text{mitigation cost trading balance}_{t,r}} = 0
    $$

    A single global carbon price is used to convert the financial flow
    (`mitigation_cost_trading_balance`) into a flow of attributed emission reductions
    (`emission_reduction_trading_balance`):

    $$
    \href{./#var__emission_reduction_trading_balance}{\text{emission reduction trading balance}_{t,r}} = \frac{\href{./#var__mitigation_cost_trading_balance}{\text{mitigation cost trading balance}_{t,r}}}{\href{./#var__global_carbon_price}{\text{global carbon price}_{t}}},
    $$

    where the global carbon price is the population weighted average of the regional carbon prices:

    $$
    \href{./#var__global_carbon_price}{\text{global carbon price}_{t}} = \frac{\sum_r \href{./#var__carbon_price}{\text{carbon price}_{t,r}} \cdot \href{./#param__timeandregional.population}{\text{population}_{t,r}}}{\sum_r \href{./#param__timeandregional.population}{\text{population}_{t,r}}}.
    $$

    The emission reductions attributed to a region are calculated as the physical reductions in that region plus its
    emission reduction trading balance:

    $$
    \href{./#var__attributed_emission_reductions}{\text{attributed emission reductions}_{t,r}} = \href{./#var__regional_emission_reductions}{\text{regional emission reductions}_{t,r}} + \href{./#var__emission_reduction_trading_balance}{\text{emission reduction trading balance}_{t,r}}.
    $$

    Regional emission allowances are the baseline emissions minus the reductions attributed to the region:

    $$
    \href{./#var__regional_emission_allowances}{\text{regional emission allowances}_{t,r}} = \href{./#var__baseline_emissions}{\text{baseline emissions}_{t,r}} - \href{./#var__attributed_emission_reductions}{\text{attributed emission reductions}_{t,r}}.
    $$

    """
    constraints = []

    m.global_carbon_price = Var(
        m.t,
        doc="Population-weighted average of regional carbon prices, used to value emission trades.",
    )

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
        m.t,
        m.regions,
        units=quant.unit("emissionsrate_unit"),
        doc="Emission reductions attributed to a region after trading, equal to its physical emission reductions plus its emission-reduction trading balance.",
    )
    m.regional_emission_allowances = Var(
        m.t,
        m.regions,
        units=quant.unit("emissionsrate_unit"),
        doc="Regional emission allowances, equal to baseline emissions minus the emission reductions attributed to the region after trading.",
    )
    m.emission_reduction_trading_balance = Var(
        m.t,
        m.regions,
        units=quant.unit("emissionsrate_unit"),
        doc="Difference between attributed and physical emission reductions due to trading. Positive values increase the reductions attributed to the region; negative values decrease them.",
    )
    m.mitigation_cost_trading_balance = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        doc="Net payment for emission trading, added to domestic mitigation costs. Positive values are payments and negative values are revenues; the balances sum to zero across regions.",
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
                    m.regional_emission_reductions[t, r]
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
