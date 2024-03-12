"""
Model equations and constraints:
Emissions and temperature
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    value,
    quant,
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
    constraints = (
        _get_emissions_constraints(m)
        + _get_temperature_constraints(m)
        + _get_inertia_and_budget_constraints(m)
    )

    return constraints


def _get_emissions_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    ## Baseline emissions

    In MIMOSA, emissions are represented by CO<sub>2</sub> emissions only[^1]. The emissions are calculated
    relative to baseline emissions: emissions that would occur in the absence of any climate policy.

    There are two ways to calculate baseline emissions: either directly imported exogenously from
    the SSP scenarios, or calculated from the baseline carbon intensity from the SSPs. The latter
    accounts for the fact that in the absence of climate policy, baseline emissions would go down if
    the GDP goes down, and vice versa. This can be chosen with the parameter [`baseline_carbon_intensity`](../parameters.md#emissions.baseline carbon intensity).
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
    - param::baseline_carbon_intensity
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
        initialize=lambda m, t, r: m.baseline_emissions(m.year(t), r),
        units=quant.unit("emissionsrate_unit"),
    )
    m.baseline_carbon_intensity = Param(doc="::emissions.baseline carbon intensity")

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
            RegionalConstraint(
                lambda m, t, r: (
                    (
                        m.baseline[t, r]
                        == m.carbon_intensity(m.year(t), r) * m.GDP_net[t, r]
                    )
                    if value(m.baseline_carbon_intensity)
                    else (m.baseline[t, r] == m.baseline_emissions(m.year(t), r))
                ),
                name="baseline_emissions",
            ),
            # Regional emissions from baseline and relative abatement
            RegionalConstraint(
                lambda m, t, r: (
                    m.regional_emissions[t, r]
                    == (1 - m.relative_abatement[t, r])
                    * (
                        m.baseline[t, r]
                        if value(m.baseline_carbon_intensity)
                        else m.baseline_emissions(m.year(t), r)
                        # Note: this should simply be m.baseline[t,r], but this is numerically less stable
                        # than m.baseline_emissions(m.year(t), r) whenever baseline intensity
                        # is used instead of baseline emissions. In fact, m.baseline_emissions(m.year(t), r)
                        # is just a fixed number, whereas m.baseline[t,r] is a variable depending on
                        # GDP.
                    )
                    if t > 0
                    else Constraint.Skip
                ),
                "regional_abatement",
            ),
            RegionalInitConstraint(
                lambda m, r: m.regional_emissions[0, r]
                == m.baseline_emissions(m.year(0), r)
            ),
            RegionalConstraint(
                lambda m, t, r: m.regional_emission_reduction[t, r]
                == m.baseline[t, r] - m.regional_emissions[t, r],
                "regional_emission_reduction",
            ),
            # Global emissions (sum from regional emissions)
            GlobalConstraint(
                lambda m, t: (
                    m.global_emissions[t]
                    == sum(m.regional_emissions[t, r] for r in m.regions)
                    if t > 0
                    else Constraint.Skip
                ),
                "global_emissions",
            ),
            GlobalInitConstraint(
                lambda m: m.global_emissions[0]
                == sum(m.baseline_emissions(m.year(0), r) for r in m.regions),
                "global_emissions_init",
            ),
            # Cumulative global emissions
            GlobalConstraint(
                lambda m, t: (
                    m.cumulative_emissions[t]
                    == m.cumulative_emissions[t - 1]
                    + (
                        (m.dt * (m.global_emissions[t] + m.global_emissions[t - 1]) / 2)
                        if value(m.cumulative_emissions_trapz)
                        else (m.dt * m.global_emissions[t])
                    )
                    if t > 0
                    else Constraint.Skip
                ),
                "cumulative_emissions",
            ),
            GlobalInitConstraint(lambda m: m.cumulative_emissions[0] == 0),
        ]
    )

    m.emission_relative_cumulative = Var(m.t, initialize=1)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    (
                        m.emission_relative_cumulative[t]
                        == m.cumulative_emissions[t]
                        / m.baseline_cumulative_global(m, m.year(0), m.year(t))
                    )
                    if t > 0
                    else Constraint.Skip
                ),
                name="relative_cumulative_emissions",
            ),
            GlobalInitConstraint(lambda m: m.emission_relative_cumulative[0] == 1),
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
            GlobalConstraint(
                lambda m, t: m.temperature[t]
                == m.T0 + m.TCRE * m.cumulative_emissions[t],
                "temperature",
            ),
            GlobalInitConstraint(lambda m: m.temperature[0] == m.T0),
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
    m.no_pos_emissions_after_budget_year = Param(
        doc="::emissions.not positive after budget year"
    )
    m.non_increasing_emissions_after_2100 = Param(
        doc="::emissions.non increasing emissions after 2100"
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
            GlobalConstraint(lambda m, t: m.cumulative_emissions[t] >= 0),
            # Global and regional inertia constraints:
            GlobalConstraint(
                lambda m, t: (
                    m.global_emissions[t] - m.global_emissions[t - 1]
                    >= m.dt
                    * m.inertia_global
                    * sum(m.baseline_emissions(m.year(0), r) for r in m.regions)
                    if value(m.inertia_global) is not False and t > 0
                    else Constraint.Skip
                ),
                name="global_inertia",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.regional_emissions[t, r] - m.regional_emissions[t - 1, r]
                    >= m.dt * m.inertia_regional * m.baseline_emissions(m.year(0), r)
                    if value(m.inertia_regional) is not False and t > 0
                    else Constraint.Skip
                ),
                name="regional_inertia",
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
        ]
    )

    return constraints
