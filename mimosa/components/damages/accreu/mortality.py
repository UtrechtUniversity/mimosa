from typing import Sequence
from mimosa.common import (
    AbstractModel,
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

from .utils import adaptation_effectiveness_fct, dmg_fct_linear, dmg_fct_power


def get_constraints(m, monetise_mortality=False):
    """TODO"""

    constraints = []

    ## Heat related mortality:
    m.mortality_heat_related = Var(m.t, m.regions, units=quant.unit("billion people"))

    m.mortality_heat_related_constant = Param(
        m.regions, doc="regional::ACCREU.heat_related_mortality_perc_constant"
    )
    m.mortality_heat_related_linear = Param(
        m.regions, doc="regional::ACCREU.heat_related_mortality_perc_linear"
    )

    constraints.append(
        RegionalEquation(
            m.mortality_heat_related,
            lambda m, t, r: m.population[t, r]
            * dmg_fct_linear(
                m,
                t,
                m.mortality_heat_related_constant[r],
                m.mortality_heat_related_linear[r],
            ),
        )
    )

    ## Cold related mortality:
    m.mortality_cold_related = Var(m.t, m.regions, units=quant.unit("billion people"))

    m.mortality_cold_related_constant = Param(
        m.regions, doc="regional::ACCREU.cold_related_mortality_perc_constant"
    )
    m.mortality_cold_related_prod = Param(
        m.regions, doc="regional::ACCREU.cold_related_mortality_perc_prod"
    )
    m.mortality_cold_related_power = Param(
        m.regions, doc="regional::ACCREU.cold_related_mortality_perc_power"
    )

    constraints.append(
        RegionalEquation(
            m.mortality_cold_related,
            lambda m, t, r: m.population[t, r]
            * dmg_fct_power(
                m,
                t,
                m.mortality_cold_related_constant[r],
                m.mortality_cold_related_prod[r],
                m.mortality_cold_related_power[r],
            ),
        )
    )

    # Calculate the monetary damages from mortality, using the value of a statistical life (VSL)
    m.mortality_svl_rel_gdp_per_cap = Param(
        doc="::economics.damages.accreu.mortality_svl_rel_gdp_cap"
    )

    if monetise_mortality:
        m.mortality_svl = Var(
            m.t, m.regions, units=quant.unit("currency_unit/population_unit")
        )
        m.mortality_damage_costs_abs = Var(
            m.t, m.regions, units=quant.unit("currency_unit")
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
            ]
        )

    return constraints
