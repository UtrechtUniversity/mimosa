from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    RegionalEquation,
    value,
    soft_max,
    soft_min,
    Any,
    exp,
    log,
    quant,
    NonNegativeReals,
)

from .utils import (
    AdaptationOptions,
    adaptation_effectiveness_fct,
    effective_adaptation_curve,
    optimal_adaptation_costs_fct,
    get_delayed_adaptation_constraint,
)


def get_constraints(m, adaptation_options: AdaptationOptions):
    """
    Adaptation for the non-SLR damages combined (labour productivity + riverine flooding).

    """

    constraints = []
    adaptation_calibration = adaptation_options.calibrations["combined"]

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
    constraints.append(
        get_delayed_adaptation_constraint("combined_labprod_riv_adaptation_costs")
    )
    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.combined_labprod_riv_avoided_damages_adapt,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.combined_labprod_riv_adaptation_costs_abs[t, r],
                    *effective_adaptation_curve(
                        m,
                        r,
                        m.combined_labprod_riv_adaptation_max_effectiveness[r],
                        m.combined_labprod_riv_adaptation_cost_param[r],
                        adaptation_calibration,
                    ),
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
                + m.labourprod_damage_costs_benefits[t, r],
            ),
        ]
    )

    if adaptation_options.uses_analytical_adaptation:
        constraints.append(
            # Calculate analytically the optimal level of adaptation
            RegionalEquation(
                m.combined_labprod_riv_adaptation_costs_abs,
                lambda m, t, r: optimal_adaptation_costs_fct(
                    m,
                    t,
                    m.combined_labprod_riv_damage_costs_gross[t, r] * m.GDP_gross[t, r],
                    *effective_adaptation_curve(
                        m,
                        r,
                        m.combined_labprod_riv_adaptation_max_effectiveness[r],
                        m.combined_labprod_riv_adaptation_cost_param[r],
                        adaptation_calibration,
                    ),
                ),
            )
        )

    return constraints
