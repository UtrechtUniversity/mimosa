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
    RegionalEquation,
    Var,
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    Without emission trading, both trading balances are always zero:

    $$
    \\begin{align}
    \\text{emission reduction trading balance}_{t,r} &= 0,\\\\
    \\text{mitigation cost trading balance}_{t,r} &= 0.
    \\end{align}
    $$

    Therefore, the reductions attributed to a region are the physical reductions within that region, and
    `mitigation_costs_abs` is equal to `domestic_mitigation_costs_abs` (see
    [Mitigation costs](mitigation.md#mitigation-costs)). The model does not create a separate
    `attributed_emission_reductions` result for this option.

    Without trade, regional emission allowances are simply equal to regional emissions:

    $$
    \\text{regional emission allowances}_{t,r} = \\text{regional emissions}_{t,r}.
    $$
    """
    constraints = []  # No constraints here

    m.emission_reduction_trading_balance = Param(
        m.t, m.regions, units=quant.unit("emissionsrate_unit"), initialize=0
    )
    m.mitigation_cost_trading_balance = Param(
        m.t, m.regions, units=quant.unit("currency_unit"), initialize=0
    )
    m.regional_emission_allowances = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )

    constraints.append(
        # When there is no emission trading, emission allowances are simply equal to the emissions
        RegionalEquation(
            m.regional_emission_allowances, lambda m, t, r: m.regional_emissions[t, r]
        )
    )

    return constraints
