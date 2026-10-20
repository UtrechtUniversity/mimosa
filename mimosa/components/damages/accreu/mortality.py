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
    """

    ### Physical impacts

    The ACCREU damage representation includes temperature-related mortality impacts, though
    without accounting for explicit adaptation. Like labour productivity, there is a heat-related
    and cold-related component, varying strongly between regions. As global mean temperature increases,
    the heat-related mortality increases, while the cold-related mortality decreases.

    The regional heat-related curve uses a [constant](#param__regional.ACCREU.heat_related_mortality_perc_constant)
    and a [temperature coefficient](#param__regional.ACCREU.heat_related_mortality_perc_prod).
    The cold-related curve has its own [constant](#param__regional.ACCREU.cold_related_mortality_perc_constant)
    and [temperature coefficient](#param__regional.ACCREU.cold_related_mortality_perc_prod).

    The mortality forecasts are sourced from Bressler et al. (2021). The paper forecasts the change in
    future heat-related and cold-related mortality rates under RCP 2.6, RCP 4.5, RCP 6.0 and RCP 8.5 scenarios.
    It does so for the 2040-59 and 2080-99 periods. For this analysis, the estimates for these ranges are assigned
    to the years 2050 and 2090 respectively. In order to convert the forecasted change in the mortality rate
    into an estimate of excess mortality, the Bressler forecasts were combined with mortality rate forecasts
    from the World Bank (2025).

    <div class="grid cards" markdown>

    -   <h5 class="no-nav">Global mortality (heat- and cold-related, without adaptation)</h5>

        ---

        ``` plotly
        {"file_path": "./assets/plots/mortality_global.json"}
        ```
    </div>

    ### Monetisation of mortality
    ...

    """

    constraints = []

    ## Heat related mortality:
    m.mortality_heat_related = Var(m.t, m.regions, units=quant.unit("billion people"))

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
    m.mortality_cold_related = Var(m.t, m.regions, units=quant.unit("billion people"))

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
    m.mortality_net = Var(m.t, m.regions, units=quant.unit("billion people"))
    constraints.append(
        RegionalEquation(
            m.mortality_net,
            lambda m, t, r: m.mortality_cold_related[t, r]
            + m.mortality_heat_related[t, r],
        )
    )

    # Calculate the monetary damages from mortality, using the value of a statistical life (VSL)
    m.mortality_svl_rel_gdp_per_cap = Param(
        initialize=inputs.config("economics.damages.accreu.mortality_svl_rel_gdp_cap")
    )

    if monetise_mortality:
        m.mortality_svl = Var(
            m.t, m.regions, units=quant.unit("currency_unit/population_unit")
        )
        m.mortality_damage_costs_abs = Var(
            m.t,
            m.regions,
            units=quant.unit("currency_unit"),
            bounds=lambda m, t, r: (
                -0.1 * m.baseline_GDP[t, r],
                0.5 * m.baseline_GDP[t, r],
            ),
        )
        m.mortality_damage_costs = Var(
            m.t, m.regions, units=quant.unit("fraction_of_GDP")
        )
        constraints.extend(
            [
                RegionalEquation(
                    m.mortality_svl,
                    lambda m, t, r: m.mortality_svl_rel_gdp_per_cap
                    * m.GDP_gross[t, r]
                    / m.population[t, r],
                ),
                RegionalEquation(
                    m.mortality_damage_costs_abs,
                    lambda m, t, r: m.mortality_svl[t, r]
                    * (m.mortality_heat_related[t, r] + m.mortality_cold_related[t, r]),
                ),
                RegionalEquation(
                    m.mortality_damage_costs,
                    lambda m, t, r: m.mortality_damage_costs_abs[t, r]
                    / m.GDP_gross[t, r],
                ),
            ]
        )

    return constraints
