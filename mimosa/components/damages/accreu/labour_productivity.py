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

from .utils import adaptation_effectiveness_fct, dmg_fct_linear


def get_constraints(m, with_combined_adaptation=True):
    """TODO"""

    constraints = []

    ## Gross damages:

    m.labourprod_damage_costs_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.labourprod_damages_gross_constant = Param(
        m.regions, doc="regional::ACCREU.labourprod_noadapt_ead_constant"
    )
    m.labourprod_damages_gross_linear = Param(
        m.regions, doc="regional::ACCREU.labourprod_noadapt_ead_linear"
    )

    constraints.append(
        RegionalEquation(m.labourprod_damage_costs_gross, gross_dmg_fct_labourprod)
    )

    ## Benefits from less cooling demand due to higher temperatures (negative damages):

    m.labourprod_damage_costs_benefits = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.labourprod_damages_benefits_constant = Param(
        m.regions, doc="regional::ACCREU.labourprod_benefit_cdd_constant"
    )
    m.labourprod_damages_benefits_linear = Param(
        m.regions, doc="regional::ACCREU.labourprod_benefit_cdd_linear"
    )

    constraints.append(
        RegionalEquation(
            m.labourprod_damage_costs_benefits, benefits_dmg_fct_labourprod
        )
    )

    ## Adaptation (only for costs, doesn't apply to benefits):

    if not with_combined_adaptation:

        m.labourprod_adaptation_costs_abs = Var(
            m.t,
            m.regions,
            units=quant.unit("currency_unit"),
            bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
        )
        m.labourprod_adaptation_costs_abs_optimal = Var(
            m.t, m.regions, units=quant.unit("currency_unit")
        )
        m.labourprod_adaptation_costs = Var(
            m.t, m.regions, units=quant.unit("fraction_of_GDP")
        )
        m.labourprod_avoided_damages_adapt = Var(
            m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
        )
        m.labourprod_damage_costs_residual = Var(
            m.t, m.regions, units=quant.unit("fraction_of_GDP")
        )
        m.labourprod_damage_costs = Var(
            m.t, m.regions, units=quant.unit("fraction_of_GDP")
        )

        m.labourprod_adaptation_max_effectiveness = Param(
            m.regions,
            doc="regional::ACCREU.labourprod_adapt_eff_max_effectiveness",
        )
        m.labourprod_adaptation_cost_param = Param(
            m.regions,
            doc="regional::ACCREU.labourprod_adapt_eff_cost_param",
        )

        constraints.extend(
            [
                # Adaptation effectiveness function
                RegionalEquation(
                    m.labourprod_avoided_damages_adapt,
                    lambda m, t, r: adaptation_effectiveness_fct(
                        m.labourprod_adaptation_costs_abs[t, r],
                        m.labourprod_adaptation_max_effectiveness[r],
                        m.labourprod_adaptation_cost_param[r],
                    ),
                ),
                # Adaptation costs as a fraction of GDP
                RegionalEquation(
                    m.labourprod_adaptation_costs,
                    lambda m, t, r: m.labourprod_adaptation_costs_abs[t, r]
                    / m.GDP_gross[t, r],
                ),
                # Residual damages after adaptation
                RegionalEquation(
                    m.labourprod_damage_costs_residual,
                    lambda m, t, r: m.labourprod_damage_costs_gross[t, r]
                    * (1 - m.labourprod_avoided_damages_adapt[t, r]),
                ),
                # Total damages after adaptation
                RegionalEquation(
                    m.labourprod_damage_costs,
                    lambda m, t, r: m.labourprod_damage_costs_residual[t, r]
                    + m.labourprod_damage_costs_benefits[t, r]
                    + m.labourprod_adaptation_costs[t, r],
                ),
            ]
        )

    return constraints


def gross_dmg_fct_labourprod(m, t, r):

    a = m.labourprod_damages_gross_constant[r]
    b = m.labourprod_damages_gross_linear[r]
    return dmg_fct_linear(m, t, a, b)


def benefits_dmg_fct_labourprod(m, t, r):

    a = m.labourprod_damages_benefits_constant[r]
    b = m.labourprod_damages_benefits_linear[r]
    return dmg_fct_linear(m, t, a, b)
