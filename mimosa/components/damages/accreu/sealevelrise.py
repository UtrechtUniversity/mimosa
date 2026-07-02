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

from .utils import adaptation_effectiveness_fct, dmg_fct_power


def get_constraints(m):
    """TODO"""

    constraints = []

    ## Gross damages:

    m.slr_damage_costs_gross = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    m.slr_damages_gross_constant = Param(
        m.regions, doc="regional::ACCREU.slr_noadapt_ead_constant"
    )
    m.slr_damages_gross_prod = Param(
        m.regions, doc="regional::ACCREU.slr_noadapt_ead_prod"
    )
    m.slr_damages_gross_power = Param(
        m.regions, doc="regional::ACCREU.slr_noadapt_ead_power"
    )

    constraints.append(
        RegionalEquation(
            m.slr_damage_costs_gross,
            lambda m, t, r: dmg_fct_power(
                m,
                t,
                m.slr_damages_gross_constant[r],
                m.slr_damages_gross_prod[r],
                m.slr_damages_gross_power[r],
                x="total_SLR",
            ),
        )
    )

    ## Adaptation:

    m.slr_adaptation_costs_abs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
    )
    m.slr_adaptation_costs_abs_optimal = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )
    m.slr_adaptation_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.slr_avoided_damages_adapt = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.slr_damage_costs_residual = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.slr_damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    m.slr_adaptation_max_effectiveness = Param(
        m.regions,
        doc="regional::ACCREU.slr_adapt_eff_max_effectiveness",
    )
    m.slr_adaptation_cost_param = Param(
        m.regions,
        doc="regional::ACCREU.slr_adapt_eff_cost_param",
    )

    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.slr_avoided_damages_adapt,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.slr_adaptation_costs_abs[t, r],
                    m.slr_adaptation_max_effectiveness[r],
                    m.slr_adaptation_cost_param[r],
                ),
            ),
            # Adaptation costs as a fraction of GDP
            RegionalEquation(
                m.slr_adaptation_costs,
                lambda m, t, r: m.slr_adaptation_costs_abs[t, r] / m.GDP_gross[t, r],
            ),
            # Residual damages after adaptation
            RegionalEquation(
                m.slr_damage_costs_residual,
                lambda m, t, r: m.slr_damage_costs_gross[t, r]
                * (1 - m.slr_avoided_damages_adapt[t, r]),
            ),
            # Total damages after adaptation
            RegionalEquation(
                m.slr_damage_costs,
                lambda m, t, r: m.slr_damage_costs_residual[t, r]
                + m.slr_adaptation_costs[t, r],
            ),
        ]
    )

    return constraints
