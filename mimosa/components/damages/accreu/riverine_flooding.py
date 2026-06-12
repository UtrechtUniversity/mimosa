from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    value,
    soft_max,
    Any,
    exp,
    quant,
    NonNegativeReals,
)

from .utils import adaptation_effectiveness_fct


def get_constraints(m):
    """TODO"""

    constraints = []

    ## Gross damages:

    m.riverine_damage_costs_gross_abs = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )
    m.riverine_damage_costs_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.riverine_damages_gross_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_constant"
    )
    m.riverine_damages_gross_time_div_100_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_time_div_100_linear"
    )
    m.riverine_damages_gross_time_div_100_squared = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_time_div_100_squared"
    )
    m.riverine_damages_gross_temp_squared = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_temp_squared"
    )

    constraints.extend(
        [
            RegionalEquation(m.riverine_damage_costs_gross_abs, gross_dmg_fct_riverine),
            RegionalEquation(
                m.riverine_damage_costs_gross,
                lambda m, t, r: m.riverine_damage_costs_gross_abs[t, r]
                / m.GDP_gross[t, r],
            ),
        ]
    )

    ## Adaptation (for now global costs, but should be regional in the future):

    m.riverine_adaptation_costs_abs = Var(
        m.t, m.regions, units=quant.unit("currency_unit"), bounds=(0, 1)
    )
    m.riverine_adaptation_costs = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.riverine_avoided_damages_adapt = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.riverine_damage_costs_residual = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.riverine_damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    # Parameters are now hardcoded, but should be regionalised
    m.riverine_adaptation_max_effectiveness = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_adapt_max_effectiveness"
    )
    m.riverine_adaptation_cost_param = Param(
        m.regions,
        doc="regional::ACCREU_sectoral.riverine_adapt_cost_param_trillion_usd",
    )

    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.riverine_avoided_damages_adapt,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.riverine_adaptation_costs_abs[t, r],
                    m.riverine_adaptation_max_effectiveness[r],
                    m.riverine_adaptation_cost_param[r],
                ),
            ),
            # Adaptation costs as a fraction of GDP
            RegionalEquation(
                m.riverine_adaptation_costs,
                lambda m, t, r: m.riverine_adaptation_costs_abs[t, r]
                / m.GDP_gross[t, r],
            ),
            # Residual damages after adaptation
            RegionalEquation(
                m.riverine_damage_costs_residual,
                lambda m, t, r: m.riverine_damage_costs_gross[t, r]
                * (1 - m.riverine_avoided_damages_adapt[t, r]),
            ),
            # Total damages after adaptation
            RegionalEquation(
                m.riverine_damage_costs,
                lambda m, t, r: m.riverine_damage_costs_residual[t, r]
                + m.riverine_adaptation_costs[t, r],
            ),
        ]
    )

    return constraints


def gross_dmg_fct_riverine(m, t, r):

    a = m.riverine_damages_gross_constant[r]
    b = m.riverine_damages_gross_time_div_100_linear[r]
    c = m.riverine_damages_gross_time_div_100_squared[r]
    d = m.riverine_damages_gross_temp_squared[r]

    def fct(time, temp):
        return a + b * (time / 100) + c * (time / 100) ** 2 + d * temp**2

    return fct(m.year(t) - 2020, m.temperature[t]) - fct(
        m.year(0) - 2020, m.temperature[0]
    )
