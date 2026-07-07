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

from .utils import adaptation_effectiveness_fct, optimal_adaptation_costs_fct


def get_constraints(m, context: ModelContext):
    """
    Adaptation for the non-SLR damages combined (labour productivity + riverine flooding).

    """

    constraints = []

    ## Gross damages:

    m.combined_labprod_riv_damage_costs_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    constraints.append(
        RegionalEquation(
            m.combined_labprod_riv_damage_costs_gross,
            lambda m, t, r: m.labourprod_damage_costs_gross[t, r]
            + m.riverine_damage_costs_gross[t, r],
        )
    )

    m.combined_labprod_riv_adaptation_costs_abs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
    )
    m.combined_labprod_riv_adaptation_costs = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.combined_labprod_riv_avoided_damages_adapt = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.combined_labprod_riv_damage_costs_residual = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.combined_labprod_riv_damage_costs = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.combined_labprod_riv_adaptation_max_effectiveness = Param(
        m.regions,
        doc="regional::ACCREU.combined_adapt_eff_max_effectiveness",
    )
    m.combined_labprod_riv_adaptation_cost_param = Param(
        m.regions,
        doc="regional::ACCREU.combined_adapt_eff_cost_param",
    )

    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.combined_labprod_riv_avoided_damages_adapt,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.combined_labprod_riv_adaptation_costs_abs[t, r],
                    m.combined_labprod_riv_adaptation_max_effectiveness[r],
                    m.combined_labprod_riv_adaptation_cost_param[r],
                    m.adaptation_effectiveness_scale_factor,
                ),
            ),
            # Adaptation costs as a fraction of GDP
            RegionalEquation(
                m.combined_labprod_riv_adaptation_costs,
                lambda m, t, r: m.combined_labprod_riv_adaptation_costs_abs[t, r]
                / m.GDP_gross[t, r],
            ),
            # Residual damages after adaptation
            RegionalEquation(
                m.combined_labprod_riv_damage_costs_residual,
                lambda m, t, r: m.combined_labprod_riv_damage_costs_gross[t, r]
                * (1 - m.combined_labprod_riv_avoided_damages_adapt[t, r]),
            ),
            # Total damages after adaptation
            RegionalEquation(
                m.combined_labprod_riv_damage_costs,
                lambda m, t, r: m.combined_labprod_riv_damage_costs_residual[t, r]
                # Add labour productivity benefits to the combined non-SLR damages
                + m.labourprod_damage_costs_benefits[t, r]
                + m.combined_labprod_riv_adaptation_costs[t, r],
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
                m.combined_labprod_riv_adaptation_costs_abs,
                lambda m, t, r: optimal_adaptation_costs_fct(
                    m.combined_labprod_riv_damage_costs_gross[t, r] * m.GDP_gross[t, r],
                    m.combined_labprod_riv_adaptation_max_effectiveness[r],
                    m.combined_labprod_riv_adaptation_cost_param[r],
                ),
            )
        )

    return constraints
