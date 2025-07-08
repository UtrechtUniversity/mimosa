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
    Constraint,
    RegionalConstraint,
    RegionalEquation,
    GlobalEquation,
    RegionalSoftEqualityConstraint,
    Any,
    quant,
    value,
    soft_min,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2-9"
    params = load_params()
    params["effort sharing"]["regime"] = "per_cap_convergence"
    params["effort sharing"]["percapconv_year"] = 2050

    # Per-capita convergence needs emission trading to avoid infeasibility
    params["model"]["emissiontrade module"] = "emissiontrade"
    # And financial transfers higher than just emission trading need to be enabled
    # (therefore allowing for negative mitigation costs)
    params["economics"]["MAC"]["rel_mitigation_costs_min_level"] = -0.5
    model = MIMOSA(params)
    ```

    The per capita convergence regime allocates equal per capita emission rights to each region, starting
    from a given year (called the convergence year). The convergence year can be set with the parameter
    [`percapconv_year`](../parameters.md#effort sharing.percapconv_year) and is
    set to 2050 by default. Before this convergence year, the allowances are interpolated
    between grandfathering (current emission distribution) in 2020 and equal per capita emission rights in the convergence year.


    Therefore, two functions are needed. First, the allowances for equal per capita emissions (EPC):

    $$
    \\text{allowances}_{\\text{EPC}, t, r} = \\frac{\\text{population}_{t,r}}{\\sum_{s} \\text{population}_{t,s}} \\cdot \\text{global emissions}_{t},
    $$

    and second the allowances for grandfathering (GF):

    $$
    \\text{allowances}_{\\text{GF}, t, r} = \\frac{\\text{baseline emissions}_{0,r}}{\\sum_{s} \\text{baseline emissions}_{0,s}} \\cdot \\text{global emissions}_{t},
    $$

    :::mimosa.components.effortsharing.per_cap_convergence.percapconv_share_rule

    Finally, the allowances per region are added as constraint on the regional emissions. Since this regime needs
    [emission trading](emissiontrading.md) to avoid infeasibility, the regional emissions can be expressed as the baseline emissions
    minus the reductions that this region needs to pay for (this is not necessarily equal to the regional emissions
    in physical terms, as the region can buy or sell allowances from other regions):

    $$
    \\text{allowances}_{t,r} = \\text{baseline emissions}_{t,r} - \\text{paid for emission reductions}_{t,r}
    $$


    """
    ## Per capita convergence:
    # m.regional_per_cap_emissions = Var(
    #     m.t, m.regions, units=quant.unit("emissionsrate_unit/population_unit")
    # )
    m.percapconv_share_init = Param(
        m.regions,
        initialize=lambda m, r: m.baseline_emissions[0, r]
        / sum(m.baseline_emissions[0, s] for s in m.regions),
    )
    m.percapconv_year = Param(initialize=2050, doc="::effort sharing.percapconv_year")
    m.percapconv_share_pop = Param(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.population[t, r] / m.global_population[t],
    )

    m.percapconv_share = Param(m.t, m.regions, initialize=percapconv_share_rule)

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.percapconv_share[t, r] * m.global_emissions[t],
            lambda m, t, r: m.regional_emission_allowances[t, r],
            epsilon=None,
            absolute_epsilon=0.001,
            ignore_if=lambda m, t, r: t == 0,
            name="percapconv_rule",
        ),
    ]


def percapconv_share_rule(m, t, r):
    """
    Finally, the allowances for each region are calculated as a linear interpolation between the two before the convergence year. After the convergence year,
    only the equal per capita emissions are used:

    $$
    \\text{allowances}_{t, r} = \\begin{cases}
    x \\cdot \\text{allowances}_{\\text{GF}, t, r} + (1-x) \\cdot (\\text{allowances}_{\\text{EPC}, t, r}), & \\text{if } t < \\text{convergence year}, \\\\
    \\text{allowances}_{\\text{EPC}, t, r}, & \\text{if } t \\geq \\text{convergence year},\\\\
    \\text{allowances}_{\\text{GF},t,r}, & \\text{if } \\text{convergence year} = \\text{false}.
    \\end{cases}
    $$

    where $x$ is the linear interpolation factor, which is 1 in the first year and 0 in the convergence year:

    $$
    x = \\frac{t - t_0}{\\text{convergence year} - t_0}.
    $$

    #### Immediate per capita convergence

    If the convergence year is set to the first year, the per capita convergence is applied immediately:

    ```python hl_lines="3"
    params = load_params()
    params["effort sharing"]["regime"] = "per_cap_convergence"
    params["effort sharing"]["percapconv_year"] = 2020  # Immediate per capita convergence
    ```

    #### Grandfathering

    If the convergence year is set to `false`, the grandfathering allowance distribution is used all the time.

    ```python hl_lines="3"
    params = load_params()
    params["effort sharing"]["regime"] = "per_cap_convergence"
    params["effort sharing"]["percapconv_year"] = False  # Grandfathering all the time
    ```
    """

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
