"""
Model equations and constraints:
Emissions and temperature
"""

from typing import Sequence

import numpy as np
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    RegionalEquation,
    GlobalEquation,
    Constraint,
    value,
    quant,
    trapezoid,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    === ":octicons-cloud-24: Baseline and mitigated emissions"

        :::mimosa.components.emissions._get_emissions_constraints

    === ":fontawesome-solid-temperature-half: Temperature"

        :::mimosa.components.emissions._get_temperature_constraints

    === ":fontawesome-solid-chart-pie: Carbon budget, inertia and other restrictions"

        :::mimosa.components.emissions._get_inertia_and_budget_constraints

    """

    # First set baseline emission functions (cumulative emissions and global cumulative emissions)
    _set_baseline_emissions(m)

    constraints = (
        _get_emissions_constraints(m)
        + _get_temperature_constraints(m)
        + _get_inertia_and_budget_constraints(m)
    )

    return constraints


def _set_baseline_emissions(m: AbstractModel) -> None:

    # Create a param for the regional cumulative baseline emissions
    def _calc_cum_baseline_emissions(m, t, r):
        values_t = range(t + 1)
        values = [value(m.baseline_emissions[s, r]) for s in values_t]
        years = value(m.beginyear) + np.array(values_t) * value(m.dt)
        return trapezoid(values, years)

    m.cumulative_baseline_emissions = Param(
        m.t,
        m.regions,
        initialize=_calc_cum_baseline_emissions,
        units=quant.unit("emissions_unit"),
    )

    # And create a param for the global cumulative baseline emissions
    m.cumulative_global_baseline_emissions = Param(
        m.t,
        initialize=lambda m, t: sum(
            value(m.cumulative_baseline_emissions[t, r]) for r in m.regions
        ),
    )

    # Finally, create a param for the regional baseline carbon intensity
    m.baseline_carbon_intensity = Param(
        m.t,
        m.regions,
        initialize=lambda m, t, r: (
            m.baseline_emissions[t, r] / m.baseline_GDP[t - 1 if t > 1 else t, r]
        ),
        units=quant.unit("emissionsrate_unit/currency_unit"),
    )


def _get_emissions_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    ## Baseline emissions

    In MIMOSA, emissions are represented by CO<sub>2</sub> emissions only[^1]. The emissions are calculated
    relative to baseline emissions: emissions that would occur in the absence of any climate policy.

    There are two ways to calculate baseline emissions: either directly imported exogenously from
    the SSP scenarios, or calculated from the baseline carbon intensity from the SSPs. The latter
    accounts for the fact that in the absence of climate policy, baseline emissions would go down if
    the GDP goes down, and vice versa. This can be chosen with the parameter [`use_baseline_carbon_intensity`](../parameters.md#emissions.baseline carbon intensity).
    If this parameter is set to true, baseline emissions are calculated as:

    $$
    \\text{baseline emissions}_{t,r} = \\text{baseline carbon intensity}_{t,r} \\cdot \\text{GDP}_{\\text{net}, t,r}
    $$

    ??? info "Baseline emissions values"

        <div style="overflow: scroll;" markdown>
        ``` plotly
        {"file_path": "./assets/plots/baseline_emissions.json"}
        ```
        </div>

    ## Emission reductions
    To calculate the actual emissions per region, the baseline emissions are reduced by a relative
    abatement factor, which in term is determined by the Marginal Abatement Cost curve and the carbon price
    (see [Mitigation](mitigation.md)). The regional emissions are then calculated as:

    $$
    \\text{regional emissions}_{t,r} = (1 - \\text{relative abatement}_{t,r}) \\cdot \\text{baseline emissions}_{t,r}
    $$

    In the first period, reductions are assumed to be zero:

    $$
    \\text{regional emissions}_{0,r} = \\text{baseline emissions}_{0,r}.
    $$

    ## Global and cumulative emissions

    The regional emissions are aggregated to global emissions:

    $$
    \\text{global emissions}_{t} = \\sum_r \\text{regional emissions}_{t,r},
    $$

    which are used to calculate the cumulative emissions. There are two ways to calculate them:
    using trapezoidal integration or by simply adding up all the years. The former is more accurate,
    while the latter is numerically more stable. This is chosen with the parameter [`cumulative_emissions_trapz`](../parameters.md#emissions.cumulative_emissions_trapz).

    === "Trapezoidal integration `default`"

        $$
        \\begin{aligned}
        \\text{cumulative emissions}_{t} & = \\text{cumulative emissions}_{t-1} \\\\ 
        & + \\frac{\\Delta t}{2} \\cdot (\\text{global emissions}_{t} + \\text{global emissions}_{t-1}) ,\\text{for } t > 0.
        \\end{aligned}
        $$

    === "Simple sum"

        $$
        \\text{cumulative emissions}_{t} = \\text{cumulative emissions}_{t-1} + \\Delta t \\cdot \\text{global emissions}_{t}
        $$


    ## Parameters defined in this module
    - param::use_carbon_intensity_for_baseline
    - param::cumulative_emissions_trapz

    [^1]: The effect of other greenhouse gases is implicitly accounted for in the TCRE which
        translates cumulative CO<sub>2</sub> emissions into temperature change. This assumes a linear
        relation between CO<sub>2</sub> emissions and other greenhouse gases.
    """

    constraints = []

    m.regional_emissions = Var(m.t, m.regions, units=quant.unit("emissionsrate_unit"))
    m.baseline = Var(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.baseline_emissions[t, r],
        units=quant.unit("emissionsrate_unit"),
    )
    m.use_carbon_intensity_for_baseline = Param(
        doc="::emissions.baseline carbon intensity"
    )

    m.relative_abatement = Var(
        m.t,
        m.regions,
        initialize=0,
        bounds=(0, 2.5),
        units=quant.unit("fraction_of_baseline_emissions"),
    )
    m.regional_emission_reduction = Var(
        m.t, m.regions, units=quant.unit("emissionsrate_unit")
    )
    m.cumulative_emissions = Var(m.t, units=quant.unit("emissions_unit"))
    m.global_emissions = Var(m.t, units=quant.unit("emissionsrate_unit"))

    m.cumulative_emissions_trapz = Param(doc="::emissions.cumulative_emissions_trapz")

    constraints.extend(
        [
            # Baseline emissions based on emissions or carbon intensity
            RegionalEquation(
                m.baseline,
                lambda m, t, r: (
                    (
                        m.baseline_carbon_intensity[t, r]
                        * (m.GDP_net[t - 1, r] if t > 1 else m.GDP_gross[t, r])
                    )
                    if value(m.use_carbon_intensity_for_baseline)
                    else m.baseline_emissions[t, r]
                ),
            ),
            # Regional emissions from baseline and relative abatement
            RegionalEquation(
                m.regional_emissions,
                lambda m, t, r: (
                    (1 - m.relative_abatement[t, r])
                    * (
                        m.baseline[t, r]
                        if value(m.use_carbon_intensity_for_baseline)
                        else m.baseline_emissions[t, r]
                    )
                    if t > 0
                    else m.baseline_emissions[0, r]
                ),
            ),
            RegionalEquation(
                m.regional_emission_reduction,
                lambda m, t, r: m.baseline[t, r] - m.regional_emissions[t, r],
            ),
            # Global emissions (sum from regional emissions)
            GlobalEquation(
                m.global_emissions,
                lambda m, t: sum(m.regional_emissions[t, r] for r in m.regions),
            ),
            # Cumulative emissions
            GlobalEquation(
                m.cumulative_emissions,
                lambda m, t: (
                    m.cumulative_emissions[t - 1]
                    + (
                        (m.dt * (m.global_emissions[t] + m.global_emissions[t - 1]) / 2)
                        if value(m.cumulative_emissions_trapz)
                        else (m.dt * m.global_emissions[t])
                    )
                    if t > 0
                    else 0
                ),
            ),
        ]
    )

    m.emission_relative_cumulative = Var(m.t, initialize=1)
    constraints.extend(
        [
            GlobalEquation(
                m.emission_relative_cumulative,
                lambda m, t: (
                    m.cumulative_emissions[t]
                    / m.cumulative_global_baseline_emissions[t]
                    if t > 0
                    else 1
                ),
            ),
        ]
    )

    return constraints


def _get_temperature_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    The global temperature change is calculated as a linear function of cumulative emissions, with a slope
    given by the Transient Climate Response to CO<sub>2</sub> Emissions (TCRE), following [Dietz et al.] who
    showed that this performed better than the default two-box DICE climate module.

    $$
    \\text{temperature}_{t} = T_0 + \\text{TCRE} \\cdot \\text{cumulative emissions}_{t},
    $$

    where [$T_0$](../parameters.md#temperature.initial) is the initial temperature at the start of the run (by default in 2020),
    and the [TCRE](../parameters.md#temperature.TCRE) is the Transient Climate Response to CO<sub>2</sub> Emissions.

    The initial temperature is set to 1.16°C in 2020 by default, following [Visser et al.]. The TCRE
    is calibrated on the IPCC AR5 or AR6 reports (the median value of the TCRE is the same in the AR5
    and AR6 calibration), but the distribution is different.

    ??? info "Calibration of the TCRE"

        The TCRE is calibrated on the IPCC AR5 and AR6 reports, both using the linear relation shown in the SPM figure of the WG1 report.
        The default value of the TCRE is 0.62°C per 1000 GtCO<sub>2</sub> (median value of the AR5 and AR6 calibration). The 5th and 95th percentiles
        differ between the two calibrations, with the AR5 calibration having a wider distribution:

        | Percentile | AR5 TCRE <br><span style="font-weight: normal">(°C per TtCO<sub>2</sub>)</span> | AR6 TCRE <br><span style="font-weight: normal">(°C per TtCO<sub>2</sub>)</span> |
        |------------|----------|----------|
        | 5th        | 0.42     | 0.42     |
        | 50th       | 0.62     | 0.62 `default` |
        | 95th       | 0.82     | 0.75     |

        === "Calibrated on IPCC AR5"

            <div style="overflow: scroll;" markdown>
            ``` plotly
            {"file_path": "./assets/plots/ar5_tcre.json"}
            ```
            </div>
            Source: [IPCC AR5 WG1 Figure SPM.10](https://www.ipcc.ch/report/ar5/wg1/summary-for-policymakers/figspm-10/)

        === "Calibrated on IPCC AR6"

            <div style="overflow: scroll;" markdown>
            ``` plotly
            {"file_path": "./assets/plots/ar6_tcre.json"}
            ```
            </div>

            Source: [IPCC AR6 WG1 Figure SPM.10](https://www.ipcc.ch/report/ar6/wg1/figures/summary-for-policymakers/figure-spm-10)

    ## Temperature target
    The usual way to specify a policy target in MIMOSA is using carbon budgets. However, it is also possible to
    specify a temperature target. This is done by setting the parameter [`temperature_target`](../parameters.md#temperature.target).
    This is an upper bound on the temperature: if the cost-optimal temperature is below this value, this constraint is not binding.

    If this parameter is set, the following constraint is active:

    $$
    \\text{temperature}_{t} \\leq \\text{temperature target}
    $$

    ## Parameters defined in this module
    - param::T0
    - param::TCRE
    - param::temperature_target
    """

    constraints = []

    m.T0 = Param(units=quant.unit("degC_above_PI"), doc="::temperature.initial")
    m.temperature = Var(
        m.t, initialize=lambda m, t: m.T0, units=quant.unit("degC_above_PI")
    )
    m.TCRE = Param(doc="::temperature.TCRE")
    m.temperature_target = Param(doc="::temperature.target")
    constraints.extend(
        [
            GlobalEquation(
                m.temperature,
                lambda m, t: (
                    m.T0 + m.TCRE * m.cumulative_emissions[t] if t > 0 else m.T0
                ),
            ),
            GlobalConstraint(
                lambda m, t: (
                    m.temperature[t] <= m.temperature_target
                    if (m.year(t) >= 2100 and value(m.temperature_target) is not False)
                    else Constraint.Skip
                ),
                name="temperature_target",
            ),
        ]
    )

    m.perc_reversible_damages = Param(doc="::economics.damages.percentage reversible")

    # m.overshoot = Var(m.t, initialize=0)
    # m.overshootdot = DerivativeVar(m.overshoot, wrt=m.t)
    # m.netnegative_emissions = Var(m.t)
    # global_constraints.extend(
    #     [
    #         lambda m, t: m.netnegative_emissions[t]
    #         == m.global_emissions[t] * (1 - tanh(m.global_emissions[t] * 10)) / 2
    #         if value(m.perc_reversible_damages) < 1
    #         else Constraint.Skip,
    #         lambda m, t: m.overshootdot[t]
    #         == (m.netnegative_emissions[t] if t <= value(m.year2100) and t > 0 else 0)
    #         if value(m.perc_reversible_damages) < 1
    #         else Constraint.Skip,
    #     ]
    # )

    # global_constraints_init.extend([lambda m: m.overshoot[0] == 0])

    return constraints


def _get_inertia_and_budget_constraints(
    m: AbstractModel,
) -> Sequence[GeneralConstraint]:
    """
    MIMOSA allows several types of constraints on emissions: a global carbon budget, inertia constraints,
    limits on net negative emissions and constraints on emissions after 2100.

    ## Carbon budget

    By default, the carbon budget is set to `False`, which means that MIMOSA runs in CBA mode without carbon budget.
    If a carbon budget is defined using the parameter [`carbonbudget`](../parameters.md#emissions.carbonbudget), the following constraint is active:

    $$
    \\text{cumulative emissions}_{t} - \\text{budget} \\leq 0,
    $$

    for $t \\geq 2100$. Note that the [`carbonbudget`](../parameters.md#emissions.carbonbudget) parameter unit should be
    in GtCO<sub>2</sub> (or TtCO<sub>2</sub> or MtCO<sub>2</sub>).

    ## Inertia

    In MIMOSA, there is a limit on how fast emissions can be reduced. This constraint is called inertia, and represents the
    technological, social, political and economic difficulties of quickly reducing emissions. It is implemented as a hard limit
    on the speed of emission reductions. The parameters [`inertia_global`](../parameters.md#emissions.inertia.global) and
    [`inertia_regional`](../parameters.md#emissions.inertia.regional) are defined as percentages of baseline emissions in the
    initial year. If baseline emissions in a region are 10 GtCO<sub>2</sub>/yr in the initial year, and the global inertia is 5%,
    then the global emissions cannot be reduced by more than 0.5 GtCO<sub>2</sub>/yr throughout the whole run. This way, the parameter
    is independent of the size of the region.

    === "Global inertia"


        $$
        \\text{global emissions}_{t} - \\text{global emissions}_{t-1} \\geq \\Delta t \\cdot \\text{inertia_global} \\cdot \\text{scaling factor},
        $$

        with the scaling factor the global baseline emissions in the starting year:

        $$
        \\text{scaling factor} = \\left( \\sum_r \\text{baseline emissions}_{t=0,r}\\right)
        $$

        By default, the [`inertia_global`](../parameters.md#emissions.inertia.global) is set to `False`, such that there is no global inertia
        constraint. The only inertia constraint happens regionally by default.

    === "Regional inertia"

        $$
        \\text{regional emissions}_{t,r} - \\text{regional emissions}_{t-1,r} \\geq \\Delta t \\cdot \\text{inertia_regional} \\cdot \\text{baseline emissions}_{t=0,r}.
        $$

        By default, the [`inertia_regional`](../parameters.md#emissions.inertia.regional) parameter is active, such that regional emissions cannot be reduced by more than 5% of the initial baseline emissions per year. This is
        based on maximum reduction speeds of the scenarios in the scenario explorer for 1.5°C pathways underpinning the IPCC Special Report on Global Warming
        of 1.5°C (<https://data.ene.iiasa.ac.at/iamc-1.5c-explorer>) (ref https://www.frontiersin.org/articles/10.3389/fclim.2021.785577/full)


    ## Minimum emission levels (limits to net-negative emissions)

    Since the Marginal Abatement Cost curve is a continuous function with no upper bound, reductions can theoretically be without bound.
    To still address the difficulties associated with CDR technologies, a limit on (net) negative emissions can be imposed. These difficulties
    can be of economic (e.g., land becoming increasingly scarce or increased dependence on very expensive storage sites) and socio-political
    (concerns about biodiversity and food security) nature (TODO ref Hotelling-Hof-Wijst paper and Fuss et al.). By the default, the global emissions
    are limited to -20 GtCO<sub>2</sub>/yr, and regionally to -10 GtCO<sub>2</sub>:

    $$
    \\text{global emissions}_t \\geq \\text{global min level},
    $$

    $$
    \\text{regional emissions}_t \\geq \\text{regional min level}.
    $$

    Note that currently, the minimum regional emission level is the same for every region, but this could be easily changed if needed (see
    [Extending MIMOSA](../extending/index.md)).

    ## Constraints on emissions after 2100

    In CBA mode, it can be useful to run MIMOSA until 2150 instead of 2100, to avoid end-of-horizon effects. One way to mitigate
    this effect is to impose a constraint on the growth of emissions after 2100. By default, emissions are not allowed to grow after 2100:

    $$
    \\text{regional emissions}_{t,r} - \\text{regional emissions}_{t-1,r} \\leq 0, \\text{if } t - 1 > 2100,
    $$

    if the parameter [`non_increasing_emissions_after_2100`](../parameters.md#emissions.non increasing emissions after 2100) is set to `True`.

    When a carbon budget is imposed, it is also possible to impose a net-zero emissions constraint after the budget year (2100):

    $$
    \\text{global emissions}_{t} \\leq 0, \\text{if } t \\geq 2100,
    $$
    if the parameter [`no_pos_emissions_after_budget_year`](../parameters.md#emissions.not positive after budget year) is set to `True`,
    **and** if a carbon budget is specified. Otherwise, this constraint is ignored.


    ## Parameters defined in this module
    - param::budget
    - param::inertia_global
    - param::inertia_regional
    - param::global_min_level
    - param::regional_min_level
    - param::no_pos_emissions_after_budget_year
    - param::non_increasing_emissions_after_2100

    """

    constraints = []

    m.budget = Param(doc="::emissions.carbonbudget")
    m.inertia_global = Param(doc="::emissions.inertia.global")
    m.inertia_regional = Param(doc="::emissions.inertia.regional")
    m.global_min_level = Param(doc="::emissions.global min level")
    m.regional_min_level = Param(doc="::emissions.regional min level")
    m.non_increasing_emissions_after_2100 = Param(
        doc="::emissions.non increasing emissions after 2100"
    )
    m.no_pos_emissions_after_budget_year = Param(
        doc="::emissions.not positive after budget year"
    )
    constraints.extend(
        [
            # Carbon budget constraints:
            GlobalConstraint(
                lambda m, t: (
                    m.cumulative_emissions[t]
                    - (
                        m.budget
                        + (
                            m.overshoot[t] * (1 - m.perc_reversible_damages)
                            if value(m.perc_reversible_damages) < 1
                            else 0
                        )
                    )
                    <= 0
                    if (m.year(t) >= 2100 and value(m.budget) is not False)
                    else Constraint.Skip
                ),
                name="carbon_budget",
            ),
            GlobalConstraint(lambda m, t: m.cumulative_emissions[t] >= 0),
            # Global and regional inertia constraints:
            GlobalConstraint(
                lambda m, t: (
                    m.global_emissions[t] - m.global_emissions[t - 1]
                    >= m.dt
                    * m.inertia_global
                    * sum(m.baseline_emissions[0, r] for r in m.regions)
                    if value(m.inertia_global) is not False and t > 0
                    else Constraint.Skip
                ),
                name="global_inertia",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.regional_emissions[t, r] - m.regional_emissions[t - 1, r]
                    >= m.dt * m.inertia_regional * m.baseline_emissions[0, r]
                    if value(m.inertia_regional) is not False and t > 0
                    else Constraint.Skip
                ),
                name="regional_inertia",
            ),
            GlobalConstraint(
                lambda m, t: (
                    m.global_emissions[t] >= m.global_min_level
                    if value(m.global_min_level) is not False
                    else Constraint.Skip
                ),
                "global_min_level",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.regional_emissions[t, r] >= m.regional_min_level
                    if value(m.regional_min_level) is not False
                    else Constraint.Skip
                ),
                "regional_min_level",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.regional_emissions[t, r] - m.regional_emissions[t - 1, r] <= 0
                    if m.year(t - 1) > 2100
                    and value(m.non_increasing_emissions_after_2100)
                    else Constraint.Skip
                ),
                name="non_increasing_emissions_after_2100",
            ),
            GlobalConstraint(
                lambda m, t: (
                    m.global_emissions[t] <= 0
                    if (
                        m.year(t) >= 2100
                        and value(m.no_pos_emissions_after_budget_year) is True
                        and value(m.budget) is not False
                    )
                    else Constraint.Skip
                ),
                name="net_zero_after_2100",
            ),
        ]
    )

    return constraints
