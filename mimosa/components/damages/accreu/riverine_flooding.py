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
    """
    Defines the equations for the gross damages, residual damages, and
    adaptation costs for riverine flooding.
    """
    constraints = []

    # Riverine flooding damages (net of avoided damages)
    m.damage_costs_riverine_flooding = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    # Riverine flooding damages (gross)
    m.gross_damage_costs_riverine_flooding = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    # Riverine flooding

    #riverine flooding adaptation costs param from CSV
    m.riverine_adaptation_param = Param(m.regions, doc="regional::ACCREU_params_MIMOSA.riverine_adapt_eff_cost_param")

    #params for riverine flooding damage function from CSV
    m.riverine_damage_a = Param(m.regions, doc="regional::ACCREU_params_MIMOSA.riverine_noadapt_ead_constant")
    m.riverine_damage_b = Param(m.regions, doc="regional::ACCREU_params_MIMOSA.riverine_noadapt_ead_linear")
    m.riverine_damage_c = Param(m.regions, doc="regional::ACCREU_params_MIMOSA.riverine_noadapt_ead_quadratic")

    ##################
    ### Step 1: gross damages
    ##################

    # Define the gross damages as a function of temperature increase:

    constraints.append(
        RegionalEquation(
            m.gross_damage_costs_riverine_flooding,
            lambda m, t, r:
            damage_fct_riverine(
                m.temp[t],
                m.riverine_damage_a[r],
                m.riverine_damage_b[r],
                m.riverine_damage_c[r]
            )
        )
    )

    ##################
    ### Step 2: Avoided damages
    ##################

    m.riverine_avoided_damages = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.riverine_adaptation_costs_abs = Var(
        m.t, m.regions, units=quant.unit("trillion USD2010/yr")
    )

    constraints.append(RegionalEquation(m.riverine_avoided_damages, riverine_avoided_damage_eq))

    ##################
    ### Step 3: residual damages and adaptation costs
    ##################

    # Total riverine damages are the sum of gross damages minus
    # avoided damages plus adaptation costs
    constraints.append(
        RegionalEquation(
            m.damage_costs_riverine_flooding,
            lambda m, t, r: (
                m.gross_damage_costs_riverine_flooding[t, r]
                * (1 - m.riverine_avoided_damages[t, r])
                + (m.riverine_adaptation_costs_abs[t, r] / m.GDP_gross[t, r] * 100)
            ),
        )
    )

    return constraints


def damage_fct_riverine(temp, a, b, c):
    """Damage function: EAD = a + b * temp + c * temp^2 with c >= 0"""

    return a + b * temp + c * temp**2


def riverine_avoided_damage_eq(m, t, r):
    """
    Adaptation effectiveness function for sea-level rise (SLR) damages, based on the fitted function in ACCREU:
    Avoided damages = L * (1 - exp(-beta * adaptation_costs))
    """
    # GLOBAL PARAMETERS
    # from regressions_coefficients_GLOFRIS.CSV
    # found in: IIASA accelerator > Inflation adjusted > Outputs (Glofris)
    L = 0.077952
    beta = 0.000565968

    return L * (1 - exp(-beta * m.riverine_adaptation_param[r]))