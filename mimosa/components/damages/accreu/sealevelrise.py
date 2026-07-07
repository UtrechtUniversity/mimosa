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
    ModelContext,
)

from .utils import (
    adaptation_effectiveness_fct,
    dmg_fct_power,
    optimal_adaptation_costs_fct,
)


def get_constraints(m, context: ModelContext):
    """TODO"""

    constraints = []
    adaptation_type = context.option("damage", "ACCREU adaptation")

    ## Gross damages:

    m.slr_damages_gross_constant = Param(
        m.regions, doc="regional::ACCREU.slr_noadapt_ead_constant"
    )
    m.slr_damages_gross_prod = Param(
        m.regions, doc="regional::ACCREU.slr_noadapt_ead_prod"
    )
    m.slr_damages_gross_power = Param(
        m.regions, doc="regional::ACCREU.slr_noadapt_ead_power"
    )

    damage_cost_gross_var_name = (
        "slr_damage_costs"
        if adaptation_type == "noadaptation"
        else "slr_damage_costs_gross"
    )
    setattr(
        m,
        damage_cost_gross_var_name,
        Var(m.t, m.regions, units=quant.unit("fraction_of_GDP")),
    )
    constraints.append(
        RegionalEquation(
            getattr(m, damage_cost_gross_var_name),
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
    if adaptation_type != "noadaptation":

        m.slr_adaptation_costs_abs = Var(
            m.t,
            m.regions,
            units=quant.unit("currency_unit"),
            bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
        )
        m.slr_adaptation_costs = Var(
            m.t, m.regions, units=quant.unit("fraction_of_GDP")
        )
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
                    lambda m, t, r: m.slr_adaptation_costs_abs[t, r]
                    / m.GDP_gross[t, r],
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

        impose_optimal_adaptation = context.option(
            "damage", "ACCREU_adaptation_impose_optimal"
        )
        if impose_optimal_adaptation:
            constraints.append(
                # Calculate analytically the optimal level of adaptation
                RegionalEquation(
                    m.slr_adaptation_costs_abs,
                    lambda m, t, r: optimal_adaptation_costs_fct(
                        m.slr_damage_costs_gross[t, r] * m.GDP_gross[t, r],
                        m.slr_adaptation_max_effectiveness[r],
                        m.slr_adaptation_cost_param[r],
                        scale=0.002,
                    ),
                )
            )

    return constraints
