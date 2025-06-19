"""
Model equations and constraints:
Mitigation costs
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    RegionalEquation,
    GlobalEquation,
    Constraint,
    log,
    soft_min,
    quant,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    === ":material-chart-bell-curve-cumulative: Marginal Abatement Costs (MAC) and mitigation costs"

        :::mimosa.components.mitigation._get_mac_constraints

    === ":material-solar-power-variant-outline: Technological learning"

        :::mimosa.components.mitigation._get_learning_constraints

    """
    constraints = _get_mac_constraints(m) + _get_learning_constraints(m)

    return constraints


def _get_mac_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    In MIMOSA, the baseline emissions can be reduced by implementing a carbon price. This increases the price of
    carbon-intensive technologies relative to cleaner alternatives, which in turn leads to a reduction in emissions.

    ## Marginal Abatement Cost curve

    The carbon price required to reach a certain level of emission reduction is quantified by a Marginal Abatement
    Cost curve (MAC curve) and gives instantaneous reductions (emission reductions in a given year) relative to the
    baseline emissions. First, a global MAC curve is defined, which is then scaled for every region to give the regional
    MAC curve.

    ### Global MAC curve

    The global MAC curve is defined as function of the relative mitigation $a$ (percentage reduction of emissions compared
    to baseline emissions) and a time-dependent learning factor:

    $$
    \\text{MAC}_t(a) = \\left( \\gamma \\cdot a^{\\beta}\\right) \\cdot \\text{learning factor}_t.
    $$

    The parameters $\\gamma$ ([`MAC_gamma`](../parameters.md#economics.MAC.gamma)) and $\\beta$ ([`MAC_beta`](../parameters.md#economics.MAC.beta))
    are calibrated using the IPCC AR6 WG3 report. The learning factor depends on learning by doing and learning over time
    (see the tab "Technological learning").

    ??? info "Calibrating the MAC using the IPCC AR6 WG3 report"

        ### Step 1: calibration data source: IPCC AR6

        Specifically, Figure 3.34c from the WGIII full report has been used to calibrate the MAC,
        as it gives discounted consumption losses from mitigation as function of cumulative CO2 emissions.
        However, for this use, the figure has been slightly recreated as function of cumulative CO2 emsisions
        from 2020 to 2100, instead of cumulative CO2 emissions from 2020 to the year of net-zero, to give a more
        accurate representation of mitigation costs for scenarios that reach net zero. The resulting mitigation costs
        are:


        All costs are calculated as the NPV of GDP losses (as compared to the corresponding baseline GDP path for each
        scenario) with a fixed social discount rate of 3%/year, as used in the original IPCC AR6 figure.

        ### Step 2: fitting a function to the data

        The next step is to fit a function through the cloud of points. We assume that the MAC is a power function
        (of a certain power $\\beta$). This means that the abatement costs, being the integral of the MAC
        (area under the MAC) follows a function of power $\\beta+1$. We obtain the best fit (highest r-squared)
        with a power of $\\beta=3$, so a cubic MAC. We then perform an Ordinary Least Square regression of the function
        $a \\cdot x^4$ (a power function of $\\beta+1=4$) and obtain the best fit shown as solid black line in figure 1:

        ![Mitigation costs as GDP loss in the AR6 database](../assets/fig/calibration_ar6_mitig_costs.jpg)

        Source of underlying GDP losses: [IPCC AR6 WG3 Figure 3.34](https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-3/#figure-3-34)

        ### Step 3: calibrating MIMOSA to the fitted function

        The final step is to calibrate the MAC used in MIMOSA to the OLS fit. In MIMOSA, this means calibrating the
        parameter $\\gamma$. When using

        $$\\gamma = 2601 \\text{ \\$/tCO}_2,$$

        the MIMOSA costs align best with the OLS fit through the AR6 points (see the diamond points in the previous figure).


    ### Regional MAC curve

    The regional MAC curve is obtained by scaling the global MAC curve by a regional scaling factor, and links the
    regional carbon price to the regional relative mitigation $a_{t,r}$:

    $$
    \\begin{align}
    \\text{carbon price}_{t,r} &= \\text{MAC}_{\\text{regional},t,r}(a_{t,r})\\\\
    &= \\text{regional scaling factor}_{r} \\cdot \\text{MAC}_t(a_{t,r})\\\\
    &= \\text{regional scaling factor}_{r} \\cdot \\left( \\gamma \\cdot a_{t,r}^{\\beta}\\right) \\cdot \\text{learning factor}_t.
    \\end{align}
    $$

    The initial carbon price at time $t=0$ is set to zero:

    $$
    \\text{carbon price}_{0,r} = 0.
    $$

    :::mimosa.components.mitigation.MAC
    The regional scaling factor transforms the global MAC into a regional MAC:


    ``` plotly
    {"file_path": "./assets/plots/MAC_kappa_rel_abatement_0.75_2050.json"}
    ```

    The values of this regional scaling factor are calibrated using SSP2 MAC curves from the TIMER model (the energy
    submodule of IMAGE). By comparing the carbon price per region required to reach 75% CO<sub>2</sub> reduction in 2050 compared to baseline,
    relative to the world average, we obtain a scaling factor for the MAC.


    <h3 id="mitigation-costs">Mitigation costs</h3>
    
    The mitigation costs are calculated as area under the MAC:

    ``` {.plotly .center_align_plotly}
    {"file_path": "./assets/plots/mac_explanation.json"}
    ```

    Since the MAC is expressed in terms of relative abatement, we still need to multiply by the baseline emissions to obtain
    mitigation costs in currency unit (dollars). The area under the MAC is therefore calculated as:
    
    $$
    \\begin{align}
    \\text{area under MAC}_{t,r} &= \\left(\\int_0^{a_{t,r}} \\text{MAC}_{\\text{regional},t,r}(a)\\ da \\right) \\cdot \\text{baseline emissions}_{t,r}\\\\
    &= \\text{factor}_{t,r} \\cdot \\frac{\\gamma \\cdot a_{t,r}^{\\beta+1}}{\\beta+1} \\cdot \\text{baseline emissions}_{t,r}
    \\end{align}
    $$

    Finally, the mitigation costs used in MIMOSA are equal to the area under the MAC, plus potentially import/export of mitigation
    costs if [emission trading](emissiontrading.md) is enabled:

    $$
    \\text{mitigation costs}_{t,r} = \\text{area under MAC}_{t,r} + \\text{import/export mitigation cost balance}_{t,r}.
    $$


    ### Relative mitigation costs and minimum level of mitigation costs
    Contrary to damages, the mitigation costs are expressed in absolute dollars, not in percentage of GDP. The relative mitigation
    costs are also available as a variable:

    $$
    \\text{rel mitigation costs}_{t,r} = \\frac{\\text{mitigation costs}_{t,r}}{\\text{GDP}_{\\text{gross}, t,r}}.
    $$

    When emission trading is allowed, some regions may even have negative mitigation costs. How negative this can become can
    be configured with the parameter [`rel_mitigation_costs_min_level`](../parameters.md#economics.MAC.rel_mitigation_costs_min_level).

    $$
    \\text{rel mitigation costs}_{t,r} \\geq \\text{rel mitigation costs min level}.
    $$

    By default, this parameter is 0, meaning that the mitigation costs can not become negative.




    ## Parameters defined in this module
    - param::MAC_gamma
    - param::MAC_beta
    - param::MAC_scaling_factor
    - param::rel_mitigation_costs_min_level

    """

    constraints = []

    # MAC: linking the carbon price to the relative abatement
    m.MAC_gamma = Param(doc="::economics.MAC.gamma")
    m.MAC_beta = Param(doc="::economics.MAC.beta")
    m.MAC_scaling_factor = Param(
        m.regions,
        doc=lambda params: f'regional::MAC.{params["economics"]["MAC"]["regional calibration factor"]}',
    )  # Regional scaling of the MAC
    m.carbonprice = Var(
        m.t,
        m.regions,
        bounds=lambda m: (0, 2 * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )
    constraints.extend(
        [
            RegionalEquation(
                m.carbonprice,
                lambda m, t, r: (
                    MAC(m.relative_abatement[t, r], m, t, r) if t > 0 else 0
                ),
            ),
        ]
    )

    # Mitigation costs

    # Note that the mitigation costs are equal to the area under the MAC plus
    # potential import/export of mitigation costs (if emission trading is enabled)
    m.mitigation_costs = Var(
        m.t,
        m.regions,
        initialize=0,
        units=quant.unit("currency_unit"),
    )
    m.area_under_MAC = Var(
        m.t,
        m.regions,
        initialize=0,
        units=quant.unit("currency_unit"),
    )
    m.rel_mitigation_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.rel_mitigation_costs_min_level = Param(
        doc="::economics.MAC.rel_mitigation_costs_min_level"
    )
    constraints.extend(
        [
            RegionalEquation(
                m.mitigation_costs,
                lambda m, t, r: (
                    AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r]
                    + m.import_export_mitigation_cost_balance[t, r]
                ),
            ),
            # Extra (dummy) constraint for the variable area_under_MAC, which is the same as the mitigation costs
            # when no emission trading is enabled
            RegionalEquation(
                m.area_under_MAC,
                lambda m, t, r: AC(m.relative_abatement[t, r], m, t, r)
                * m.baseline[t, r],
            ),
            RegionalEquation(
                m.rel_mitigation_costs,
                lambda m, t, r: m.mitigation_costs[t, r] / m.GDP_gross[t, r],
            ),
            RegionalConstraint(
                lambda m, t, r: m.rel_mitigation_costs[t, r]
                >= (m.rel_mitigation_costs_min_level if t > 0 else 0.0),
                "rel_mitigation_costs_non_negative",
            ),
        ]
    )

    # Keep track of relative global costs
    m.global_rel_mitigation_costs = Var(m.t, units=quant.unit("fraction_of_GDP"))
    constraints.extend(
        [
            GlobalEquation(
                m.global_rel_mitigation_costs,
                lambda m, t: (
                    sum(m.mitigation_costs[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    # Calculate average global emission reduction per cost unit
    # and average cost per unit emission reduction

    m.global_emission_reduction_per_cost_unit = Var(
        m.t, units=quant.unit("emissionsrate_unit / currency_unit")
    )
    m.global_cost_per_emission_reduction_unit = Var(
        m.t, units=quant.unit("currency_unit / emissionsrate_unit")
    )
    constraints.extend(
        [
            GlobalEquation(
                m.global_cost_per_emission_reduction_unit,
                lambda m, t: (
                    sum(m.mitigation_costs[t, r] for r in m.regions)
                    / soft_min(
                        sum(m.regional_emission_reduction[t, r] for r in m.regions)
                    )
                    if t > 0
                    else 0
                ),
            ),
            GlobalEquation(
                m.global_emission_reduction_per_cost_unit,
                lambda m, t: (
                    sum(m.regional_emission_reduction[t, r] for r in m.regions)
                    / soft_min(sum(m.mitigation_costs[t, r] for r in m.regions))
                    if t > 0
                    else 0
                ),
            ),
        ]
    )

    return constraints


def _get_learning_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    In MIMOSA, there are two ways in which the price of mitigation policy can be reduced over time:
    through learning by doing and learning over time. The learning factor is the product of these two factors.

    ## Learning by doing

    Learning by doing (endogenous technological learning) is a process where the cost of a technology decreases as more of it is produced. Here,
    the more mitigation has been done in the previous time steps, the cheaper the marginal abatement costs (MAC) become.

    The learning by doing factor is defined as:

    $$
    \\text{LBD factor}_t = \\left( \\xi \\cdot \\text{cumulative mitigation}_t + 1 \\right)^{\\log_2(\\rho)},
    $$

    with $\\rho$ ([`LBD_rate`](../parameters.md#economics.MAC.LBD_rate)) the progress ratio (i.e., the reduction in
    costs for doubling cumulative mitigation capacity) representing empirical studies of endogenous technological
    learning (see <https://www.frontiersin.org/articles/10.3389/fclim.2021.785577/full>).

    $\\xi$ ([`LBD_scaling`](../parameters.md#economics.MAC.LBD_scaling)) is a scaling factor
    to transform the units of cumulative mitigation in relative terms (compared to baseline emissions in $t=0$).

    The cumulative mitigation is equal to:

    $$
    \\text{cumulative mitigation}_t = \\text{baseline cum. emissions}_t - \\text{cum. emissions}_t.
    $$


    ## Learning over time

    Learning over time (exogenous technological learning) is a process where the cost of technology descreases over time,
    even if no mitigation has been done yet. The learning over time factor is defined as:

    $$
    \\text{LOT factor}_t = \\frac{1}{(1 + \\lambda)^t},
    $$

    with $\\lambda$ ([`LOT_rate`](../parameters.md#economics.MAC.LOT_rate)) the learning rate. By default, the learning over time
    rate is zero, so no learning over time is assumed.

    ## Parameters defined in this module
    - param::LBD_rate
    - param::LBD_scaling
    - param::LOT_rate

    """
    constraints = []

    ### Technological learning

    # Learning by doing
    m.LBD_rate = Param(doc="::economics.MAC.LBD_rate")
    m.log_LBD_rate = Param(initialize=log(m.LBD_rate) / log(2))
    m.LBD_scaling = Param(doc="::economics.MAC.LBD_scaling")
    m.LBD_factor = Var(m.t)  # , bounds=(0,1), initialize=1)
    constraints.append(
        GlobalEquation(
            m.LBD_factor,
            lambda m, t: (
                soft_min(
                    (
                        m.cumulative_global_baseline_emissions[t - 1]
                        - m.cumulative_emissions[t - 1]  # Now changed to t-1, check
                    )
                    / m.LBD_scaling
                    + 1.0
                )
                ** m.log_LBD_rate
                if t > 0
                else 1.0
            ),
        )
    )

    # Learning over time and total learning factor
    m.LOT_rate = Param(doc="::economics.MAC.LOT_rate")
    m.LOT_factor = Var(m.t)
    m.learning_factor = Var(m.t)
    constraints.extend(
        [
            GlobalEquation(
                m.LOT_factor,
                lambda m, t: (1 / (1 + m.LOT_rate) ** t),
            ),
            GlobalEquation(
                m.learning_factor,
                lambda m, t: (m.LBD_factor[t] * m.LOT_factor[t]),
            ),
        ]
    )

    return constraints


#################
## Utils
#################


def MAC(a, m, t, r):
    factor = (
        m.learning_factor[t] * m.MAC_scaling_factor[r] * m.MAC_SSP_calibration_factor[t]
    )
    return factor * m.MAC_gamma * a**m.MAC_beta


def AC(a, m, t, r):
    factor = (
        m.learning_factor[t] * m.MAC_scaling_factor[r] * m.MAC_SSP_calibration_factor[t]
    )
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)
