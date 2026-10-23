from typing import Sequence
from mimosa.common import (
    ConcreteModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    RegionalEquation,
    GlobalEquation,
    value,
    soft_max,
    soft_min,
    Any,
    exp,
    log,
    quant,
    NonNegativeReals,
)

from mimosa.core.model_inputs import ModelInputs

from .utils import adaptation_effectiveness_fct, dmg_fct_linear, dmg_fct_power


def get_constraints(m: ConcreteModel, inputs: ModelInputs, monetise_mortality=False):
    r"""

    ### Physical impacts

    The ACCREU damage representation includes temperature-related mortality impacts, though
    without accounting for explicit adaptation. Like labour productivity, there is a heat-related
    and cold-related component, varying strongly between regions. As global mean temperature increases,
    the heat-related mortality increases, while the cold-related mortality decreases.

    The mortality forecasts are sourced from Bressler et al. (2021). The paper forecasts the change in
    future heat-related and cold-related mortality rates under RCP 2.6, RCP 4.5, RCP 6.0 and RCP 8.5 scenarios.
    It does so for the 2040-59 and 2080-99 periods. For this analysis, the estimates for these ranges are assigned
    to the years 2050 and 2090 respectively. In order to convert the forecasted change in the mortality rate
    into an estimate of excess mortality, the Bressler forecasts were combined with mortality rate forecasts
    from the World Bank (2025).

    The heat-related mortality (as % of population) was fitted with a quadratic function. Given that they represent
    additional mortality relative to 2010, the fit was relative to temperature in 2010: 1.1 °C. To obtain a mortality
    value in absolute numbers, we multiply by total population:

    $$
    \href{./#var__mortality_heat_related}{\text{mortality}_{\text{heat}, t, r}}
    = \href{./#param__timeandregional.population}{\text{population}_{t,r}}
    \cdot {\large(}
        (\href{./#param__regional.ACCREU.heat_related_mortality_perc_constant}{a_r}
        + \href{./#param__regional.ACCREU.heat_related_mortality_perc_prod}{b_r}
        \cdot (\href{./#var__temperature}{T_t} - 1.1)^2)
        - (\href{./#param__regional.ACCREU.heat_related_mortality_perc_constant}{a_r}
        + \href{./#param__regional.ACCREU.heat_related_mortality_perc_prod}{b_r}
        \cdot (\href{./#var__temperature}{T_0} - 1.1)^2)
    {\large)}
    $$

    Cold-related mortality showed a linear relation with temperature, accounting for the fact that reductions in
    cold-related mortality don't become marginally larger when temperatures become very high. In fact, at some point
    we expect to see a plateau. However, the data doesn't show this behaviour for the assessed temperature range, where
    a linear fit throughout is the best fit:

    $$
    \href{./#var__mortality_cold_related}{\text{mortality}_{\text{cold}, t, r}}
    = \href{./#param__timeandregional.population}{\text{population}_{t,r}}
    \cdot {\large(}
        (\href{./#param__regional.ACCREU.cold_related_mortality_perc_constant}{a_r}
        + \href{./#param__regional.ACCREU.cold_related_mortality_perc_prod}{b_r}
        \cdot (\href{./#var__temperature}{T_t} - 1.1))
        - (\href{./#param__regional.ACCREU.cold_related_mortality_perc_constant}{a_r}
        + \href{./#param__regional.ACCREU.cold_related_mortality_perc_prod}{b_r}
        \cdot (\href{./#var__temperature}{T_0} - 1.1))
    {\large)}
    $$

    The total mortality is the sum of both:

    $$
    \href{./#var__mortality_net}{\text{mortality}_{\text{net},t,r}}
    = \href{./#var__mortality_heat_related}{\text{mortality}_{\text{heat}, t, r}}
    + \href{./#var__mortality_cold_related}{\text{mortality}_{\text{cold}, t, r}}.
    $$


    <div class="grid cards" markdown>

    -   <h5 class="no-nav">Global mortality (heat- and cold-related, without adaptation)</h5>

        ---

        ``` plotly
        {"file_path": "./assets/plots/mortality_global.json"}
        ```
    </div>

    <div class="tiny_table table_scrollable extra_small" markdown>

    | Variables created in this module: |
    | --------------------------------- |
    | var::mortality_heat_related |
    | var::mortality_cold_related |
    | var::mortality_net |

    </div>

    ### Monetisation of mortality

    :::mimosa.components.damages.accreu.mortality._get_monetised_mortality_constraints

    """

    constraints = []

    ## Heat related mortality:
    m.mortality_heat_related = Var(
        m.t,
        m.regions,
        units=quant.unit("billion people"),
        doc="Extra heat-related mortality, in absolute numbers. Extra is compared to start year of the run (2025).",
    )

    m.mortality_heat_related_constant = Param(
        m.regions,
        initialize=inputs.regional("ACCREU", "heat_related_mortality_perc_constant"),
    )
    m.mortality_heat_related_prod = Param(
        m.regions,
        initialize=inputs.regional("ACCREU", "heat_related_mortality_perc_prod"),
    )

    constraints.append(
        RegionalEquation(
            m.mortality_heat_related,
            lambda m, t, r: m.population[t, r]
            * dmg_fct_power(
                m,
                t,
                m.mortality_heat_related_constant[r],
                m.mortality_heat_related_prod[r],
                2,
                xshift=1.1,
            ),
        )
    )

    ## Cold related mortality:
    m.mortality_cold_related = Var(
        m.t,
        m.regions,
        units=quant.unit("billion people"),
        doc="Reduced cold-related mortality, in absolute numbers, compared to start year of the run (2025).",
    )

    m.mortality_cold_related_constant = Param(
        m.regions,
        initialize=inputs.regional("ACCREU", "cold_related_mortality_perc_constant"),
    )
    m.mortality_cold_related_prod = Param(
        m.regions,
        initialize=inputs.regional("ACCREU", "cold_related_mortality_perc_prod"),
    )

    constraints.append(
        RegionalEquation(
            m.mortality_cold_related,
            lambda m, t, r: m.population[t, r]
            * dmg_fct_linear(
                m,
                t,
                m.mortality_cold_related_constant[r],
                m.mortality_cold_related_prod[r],
                xshift=1.1,
            ),
        )
    )

    ## Net mortality (heat + cold related):
    m.mortality_net = Var(
        m.t,
        m.regions,
        units=quant.unit("billion people"),
        doc="Sum of extra heat-related mortality and reduced cold-related mortality, in absolute numbers.",
    )
    constraints.append(
        RegionalEquation(
            m.mortality_net,
            lambda m, t, r: m.mortality_cold_related[t, r]
            + m.mortality_heat_related[t, r],
        )
    )

    if monetise_mortality:
        constraints.extend(_get_monetised_mortality_constraints(m, inputs))

    return constraints


def _get_monetised_mortality_constraints(m: ConcreteModel, inputs: ModelInputs):
    r"""
    If the MIMOSA parameter [monetise mortality](#param__economics.damages.accreu.monetise_mortality)
    is set to true, the mortality values are converted to monetary value, which are then used
    by the welfare function:

    ```python hl_lines="2"
    params = load_params()
    params["economics"]["damages"]["accreu"]["monetise_mortality"] = True # or False
    model = MIMOSA(params)
    ```
    
    Valuation of mortality in monetary units can be done using values of
    statistical life (VSL) or values of statistical life years (VSLY) multiplied by the expected
    life years lost. The main difference between these valuation methods is that the
    VSLY approach gives relatively lower values to mortality of people with a lower
    remaining life expectancy, while the VSL approach values mortality in all age
    classes equally.

    Here, we follow the recommendation by the OECD to not adjust valuation according
    to the age of the population as this would imply that public policy and cost-benefit
    analysis outcomes could differ solely based on differences in the age of the populations
    studied. Moreover, little is known about the expected life years lost due to climate
    change impacts (Toulemon & Barbieri, 2008).

    We therefore use the VSL approach for valuing the cost of mortality. The default MIMOSA
    value is the recommended estimates of the VSL from the OECD (2025). They provide a weighted
    world value of the VSL of 2.4 million dollars, which gives a [$\text{VSL}_{\text{rel}}$](#param__economics.damages.accreu.mortality_vsl_rel_gdp_cap)
    of 117.59 times the GDP per capita.

    The VSL in dollar terms is therefore:

    $$
    \href{./#var__mortality_vsl}{\text{VSL}_{\text{abs},t,r}}
    = \href{./#param__economics.damages.accreu.mortality_vsl_rel_gdp_cap}{\text{VSL}_{\text{rel}}}
    \cdot \frac{\href{./#var__GDP_gross}{\text{GDP}_{\text{gross},t,r}}}{\href{./#param__timeandregional.population}{\text{population}_{t,r}}}
    $$


    The resulting mortality costs (in absolute terms) are given by:

    $$
    \begin{align}
        \href{./#var__mortality_damage_costs_abs}{\text{abs. damages}_{\text{mortality}, t, r}}
        &=\href{./#var__mortality_vsl}{\text{VSL}_{\text{abs},t,r}} \cdot (\href{./#var__mortality_heat_related}{\text{mortality}_{\text{heat}, t, r}}
        + \href{./#var__mortality_cold_related}{\text{mortality}_{\text{cold}, t, r}})\\
        &= \href{./#var__non_market_damage_costs_abs}{\text{abs. damages}_{\text{non-market}, t,r}}
    \end{align}
    $$

    Since these are the only non-market damages in the model, the non-market damages are equal to the
    mortality costs. These are not subtracted from GDP, but are removed in the [welfare function](../welfare.md).
    damages. 

    <div class="tiny_table table_scrollable extra_small" markdown>

    | Variables created when mortality is monetised: |
    | --------------------------------- |
    | var::mortality_vsl |
    | var::mortality_damage_costs_abs |
    | var::mortality_damage_costs |

    </div>

    """

    # Calculate the monetary damages from mortality, using the value of a statistical life (VSL)
    m.mortality_vsl_rel_gdp_per_cap = Param(
        initialize=inputs.config("economics.damages.accreu.mortality_vsl_rel_gdp_cap")
    )

    m.mortality_vsl = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        doc="Value of statistical life (VSL) in currency units, calculated as the relative VSL times GDP per capita",
    )
    m.mortality_damage_costs_abs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        bounds=lambda m, t, r: (
            -0.1 * m.baseline_GDP[t, r],
            0.5 * m.baseline_GDP[t, r],
        ),
        doc="Mortality damage costs in currency units. Since the extra heat-related deaths and reduced cold-related deaths are considered, this value can be positive or negative, depending on the region, time, and temperature.",
    )
    m.mortality_damage_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
        doc="Mortality damage costs expressed as % of GDP",
    )
    constraints = [
        RegionalEquation(
            m.mortality_vsl,
            lambda m, t, r: m.mortality_vsl_rel_gdp_per_cap
            * m.GDP_gross[t, r]
            / m.population[t, r],
        ),
        RegionalEquation(
            m.mortality_damage_costs_abs,
            lambda m, t, r: m.mortality_vsl[t, r]
            * (m.mortality_cold_related[t, r] + m.mortality_heat_related[t, r]),
        ),
        RegionalEquation(
            m.mortality_damage_costs,
            lambda m, t, r: m.mortality_damage_costs_abs[t, r] / m.GDP_gross[t, r],
        ),
    ]

    return constraints
