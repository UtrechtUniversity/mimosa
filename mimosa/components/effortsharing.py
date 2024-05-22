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
    RegionalSoftEqualityConstraint,
    Any,
    quant,
    value,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Effort-sharing regimes can be used to enforce the redistribution of mitigation effort and damage costs among
    regions following pre-defined equity principles. By default, in MIMOSA, no effort-sharing regime is imposed.

    Besides no regime at all, there are three types of effort-sharing regimes implemented in MIMOSA. This can be
    set using the [`effort_sharing_regime`](../parameters.md#effort sharing.regime) parameter.

    === "No regime `default`"
        Usage:
        ```python hl_lines="2"
        params = load_params()
        params["effort sharing"]["regime"] = "noregime"
        model = MIMOSA(params)
        ```

        By default, no effort-sharing regime is imposed.

    === "Equal mitigation costs"

        :::mimosa.components.effortsharing._get_equal_mitigation_costs_constraints

    === "Equal total costs"

        :::mimosa.components.effortsharing._get_equal_total_costs_constraints

    === "Per capita convergence"

        :::mimosa.components.effortsharing._get_percapconv_constraints


    """

    m.effort_sharing_regime = Param(within=Any, doc="::effort sharing.regime")

    # Variable used as a common level accross various effort-sharing regimes
    # For example, in the equal_mitig_costs regime, this would be a global level of
    # mitigation costs.
    m.effort_sharing_common_level = Var(m.t, units=quant.unit("fraction_of_GDP"))

    constraints = (
        _get_equal_mitigation_costs_constraints()
        + _get_equal_total_costs_constraints()
        + _get_percapconv_constraints(m)
    )

    return constraints


def _get_equal_mitigation_costs_constraints() -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "equal_mitigation_costs"
    model = MIMOSA(params)
    ```

    Equal mitigation costs implies that the regional mitigation costs in every year (in terms of
    percentage of GDP) should be the same for every region:

    $$
    \\frac{\\text{mitig. costs}_{t,r}}{\\text{GDP}_{\\text{gross},t,r}} = \\text{common level}_t,
    $$

    where the variable $\\text{common level}_t$ can have arbitrary values and is purely used as a common
    value accross all the regions[^1].

    [^1]: Note that for numerical stability, the constraint is not implemented as an equality constraint,
        but as an "almost-equality" constraint (called soft-equality constraint). This means that it is enough
        if the left-hand side (LHS) and right-hand side (RHS) are very close to each other (less than 0.5%):

        $$
        0.995 \\cdot \\text{LHS} \\leq \\text{RHS} \\leq 1.005 \\cdot \\text{LHS}.
        $$

    """
    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.rel_mitigation_costs[t, r],
            lambda m, t, r: m.effort_sharing_common_level[t],
            "effort_sharing_regime_mitigation_costs",
            ignore_if=lambda m, t, r: value(m.effort_sharing_regime)
            != "equal_mitigation_costs",
            # or m.year(t) > 2125,
        ),
    ]


def _get_equal_total_costs_constraints() -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "equal_total_costs"
    model = MIMOSA(params)
    ```

    In this effort-sharing regime, the damages are also taken into account when equalising the costs among regions:

    $$
    \\frac{\\text{mitig. costs}_{t,r}}{\\text{GDP}_{\\text{gross},t,r}} + \\text{damages}_{t,r}\\ (+ \\text{rel. financial transf.}_{t,r}) = \\text{common level}_t,
    $$

    where the variable $\\text{common level}_t$ can have arbitrary values and is purely used as a common
    value accross all the regions[^1]. Note that the variable $\\text{damages}_{t,r}$ is already expressed as percentage of GDP (see [Damages](damages.md)).

    For feasibility reasons, this constraint is only enforced until 2100.

    Compared to the equal mitigation cost regime, this regime might be infeasible, especially for regions with very high damages, unless:

    * (a) the mitigation costs can be negative (for regions with very high damages). This can be achieved with the
        parameter [`rel_mitigation_costs_min_level`](../parameters.md#economics.MAC.rel_mitigation_costs_min_level).

    * or (b) if financial transfers are allowed between regions, that go beyond emission trading. See [Financial transfers](financialtransfers.md).

    [^1]: Note that for numerical stability, the constraint is not implemented as an equality constraint,
        but as an "almost-equality" constraint (called soft-equality constraint). This means that it is enough
        if the left-hand side (LHS) and right-hand side (RHS) are very close to each other (less than 0.5%):

        $$
        0.995 \\cdot \\text{LHS} \\leq \\text{RHS} \\leq 1.005 \\cdot \\text{LHS}.
        $$
    """

    return [
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
    ]


def _get_percapconv_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2 3 4 5 6"
    params = load_params()
    params["effort sharing"]["regime"] = "per_cap_convergence"
    params["effort sharing"]["percapconv_year"] = 2050

    # Per-capita convergence needs emission trading to avoid infeasibility
    params["model"]["emissiontrade_module"] = "emissiontrade"
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

    :::mimosa.components.effortsharing.percapconv_share_rule

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
        initialize=lambda m, t, r: m.population[t, r]
        / sum(m.population[t, s] for s in m.regions),
    )

    m.percapconv_share = Param(m.t, m.regions, initialize=percapconv_share_rule)

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.percapconv_share[t, r] * m.global_emissions[t],
            lambda m, t, r: m.regional_emission_allowances[t, r],
            epsilon=None,
            absolute_epsilon=0.001,
            ignore_if=lambda m, t, r: value(m.effort_sharing_regime)
            != "per_cap_convergence"
            or t == 0,
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

    If the convergence year is set to `false`, the grandfathering allowance distribution is used all the time.
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
