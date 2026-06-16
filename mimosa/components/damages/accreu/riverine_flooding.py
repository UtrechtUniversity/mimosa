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

from .utils import adaptation_effectiveness_fct


def get_constraints(m):
    """TODO"""

    constraints = []

    ## Gross damages:

    # m.riverine_damage_costs_gross_abs = Var(
    #     m.t, m.regions, units=quant.unit("currency_unit")
    # )
    m.riverine_damage_costs_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.riverine_damages_gross_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_noadapt_ead_constant"
    )
    m.riverine_damages_gross_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_noadapt_ead_linear"
    )
    m.riverine_damages_gross_quadr = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_noadapt_ead_quadr"
    )

    constraints.append(
        RegionalEquation(m.riverine_damage_costs_gross, gross_dmg_fct_riverine)
    )

    ## Adaptation:

    m.riverine_adaptation_costs_abs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
    )
    m.riverine_adaptation_costs_abs_optimal = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
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

    m.riverine_adaptation_max_effectiveness = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_adapt_eff_max_effectiveness"
    )
    m.riverine_adaptation_cost_param = Param(
        m.regions,
        doc="regional::ACCREU_sectoral.riverine_adapt_eff_cost_param",
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
            # Calculate analytically the optimal level of adaptation
            # RegionalConstraint(
            #     lambda m, t, r: m.riverine_adaptation_costs_abs[t, r]
            #     <= optimal_adaptation_costs_fct(
            #         m.riverine_damage_costs_gross_abs[t, r],
            #         m.riverine_adaptation_max_effectiveness[r],
            #         m.riverine_adaptation_cost_param[r],
            #     ),
            # ),
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
    b = m.riverine_damages_gross_linear[r]
    c = m.riverine_damages_gross_quadr[r]

    def fct(x):
        return a + b * x + c * x**2

    return fct(m.temperature[t]) - fct(m.temperature[0])


# def gross_dmg_fct_riverine(m, t, r):

#     a = m.riverine_damages_gross_constant[r]
#     b = m.riverine_damages_gross_time_div_100_linear[r]
#     c = m.riverine_damages_gross_time_div_100_squared[r]
#     d = m.riverine_damages_gross_temp_squared[r]

#     def fct(time, temp):
#         return a + b * (time / 100) + c * (time / 100) ** 2 + d * temp**2

#     return fct(m.year(t) - 2020, m.temperature[t]) - fct(
#         m.year(0) - 2020, m.temperature[0]
#     )


def optimal_adaptation_costs_fct(gross_damages_abs, a, b):
    if a * b == 0:
        return 0
    return soft_min(log(a * b * soft_min(gross_damages_abs, 0.01)) / b, 0.01)
