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


def get_constraints(m):
    """TODO"""

    constraints = []

    ## Gross damages:

    m.damage_costs_riverine_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.damages_gross_riverine_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_constant"
    )
    m.damages_gross_riverine_time_div_100_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_time_div_100_linear"
    )
    m.damages_gross_riverine_time_div_100_squared = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_time_div_100_squared"
    )
    m.damages_gross_riverine_temp_squared = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_temp_squared"
    )

    constraints.append(
        RegionalEquation(m.damage_costs_riverine_gross, gross_dmg_fct_riverine)
    )

    ## Adaptation (for now global costs, but should be regional in the future):

    m.adaptation_costs_riverine_abs = Var(m.t, units=quant.unit("currency_unit"))
    m.adaptation_costs_riverine = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.adaptation_riverine_avoided_damages = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.damage_costs_riverine_residual = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.damage_costs_riverine = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    # Parameters are now hardcoded, but should be regionalised
    m.adaptation_riverine_max_effectiveness = Param(initialize=0.864429)
    m.adaptation_riverine_cost_param = Param(initialize=10.262109)

    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.adaptation_riverine_avoided_damages,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.adaptation_costs_riverine_abs[t],
                    m.adaptation_riverine_max_effectiveness,
                    m.adaptation_riverine_cost_param,
                ),
            ),
            # Adaptation costs as a fraction of GDP. Now every region gets same costs as % GDP
            RegionalEquation(
                m.adaptation_costs_riverine,
                lambda m, t, r: m.adaptation_costs_riverine_abs[t]
                / m.global_GDP_gross[t],
            ),
            # Residual damages after adaptation
            RegionalEquation(
                m.damage_costs_riverine_residual,
                lambda m, t, r: m.damage_costs_riverine_gross[t, r]
                * (1 - m.adaptation_riverine_avoided_damages[t, r]),
            ),
            # Total damages after adaptation
            RegionalEquation(
                m.damage_costs_riverine,
                lambda m, t, r: m.damage_costs_riverine_residual[t, r]
                + m.adaptation_costs_riverine[t, r],
            ),
        ]
    )

    return constraints


def gross_dmg_fct_riverine(m, t, r):

    a = m.damages_gross_riverine_constant[r]
    b = m.damages_gross_riverine_time_div_100_linear[r]
    c = m.damages_gross_riverine_time_div_100_squared[r]
    d = m.damages_gross_riverine_temp_squared[r]

    def fct(time, temp):
        return a + b * (time / 100) + c * (time / 100) ** 2 + d * temp**2

    return fct(m.year(t) - 2020, m.temperature[t]) - fct(
        m.year(0) - 2020, m.temperature[0]
    )


def adaptation_effectiveness_fct(adapt_costs, max_effectiveness, cost_param):
    """
    Adaptation effectiveness function, based on the fitted function in ACCREU:
    Avoided damages = max_effectiveness * (1 - exp(-cost_param * adapt_costs))
    """

    return max_effectiveness * (1 - exp(-cost_param * adapt_costs))
