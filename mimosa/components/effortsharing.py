"""
Model equations and constraints:
Effort sharing
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    RegionalSoftEqualityConstraint,
    Any,
    quant,
    value,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emissions and temperature equations and constraints

    Necessary variables:

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.effort_sharing_regime = Param(within=Any, doc="::effort sharing.regime")

    ## effort sharing scheme:
    m.effort_sharing_common_level = Var(m.t, units=quant.unit("fraction_of_GDP"))

    constraints.extend(
        [
            # Total costs: mitigation + damage costs should be equal among regions as % GDP
            RegionalSoftEqualityConstraint(
                lambda m, t, r: m.rel_mitigation_costs[t, r]
                + m.damage_costs[t, r]
                + m.rel_financial_transfer[t, r],
                lambda m, t, r: m.effort_sharing_common_level[t],
                "effort_sharing_regime_total_costs",
                ignore_if=lambda m, t, r: value(m.effort_sharing_regime)
                != "equal_total_costs"
                or m.year(t) > 2100,
            ),
            # Mitigation costs: mitigation costs should be equal among regions as % GDP
            RegionalSoftEqualityConstraint(
                lambda m, t, r: m.rel_mitigation_costs[t, r],
                lambda m, t, r: m.effort_sharing_common_level[t],
                "effort_sharing_regime_mitigation_costs",
                ignore_if=lambda m, t, r: value(m.effort_sharing_regime)
                != "equal_mitigation_costs",
                # or m.year(t) > 2125,
            ),
        ]
    )

    ## Per capita convergence:
    # m.regional_per_cap_emissions = Var(
    #     m.t, m.regions, units=quant.unit("emissionsrate_unit/population_unit")
    # )
    m.percapconv_share_init = Param(
        m.regions,
        initialize=lambda m, r: m.baseline_emissions(m.year(0), r)
        / sum(m.baseline_emissions(m.year(0), s) for s in m.regions),
    )
    m.percapconv_year = Param(initialize=2050, doc="::effort sharing.percapconv_year")
    m.percapconv_share_pop = Param(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.population(m.year(t), r)
        / sum(m.population(m.year(t), s) for s in m.regions),
    )

    constraints.extend(
        [
            RegionalSoftEqualityConstraint(
                lambda m, t, r: percapconv_share_rule(m, t, r) * m.global_emissions[t],
                lambda m, t, r: m.baseline[t, r] - m.paid_for_emission_reductions[t, r],
                epsilon=None,
                absolute_epsilon=0.01,
                ignore_if=lambda m, t, r: value(m.effort_sharing_regime)
                != "per_cap_convergence"
                or t == 0,
                name="percapconv_rule",
            ),
        ]
    )

    return constraints


def percapconv_share_rule(m, t, r):
    year_0, year_t = m.year(0), m.year(t)
    year_conv = m.percapconv_year

    if year_conv is False:
        # If it is false, use grandfathering all the time
        return m.percapconv_share_init[r]
    if year_conv == year_0:
        # If it is equal to first year, use immediate per capita convergence
        return m.percapconv_share_pop[t, r]

    year_linear_part = (year_t - year_0) / (year_conv - year_0)

    return (
        min(year_linear_part, 1) * m.percapconv_share_pop[t, r]
        + max(1 - year_linear_part, 0) * m.percapconv_share_init[r]
    )
