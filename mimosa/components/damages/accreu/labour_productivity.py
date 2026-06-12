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

    m.damage_costs_gross_labourprod = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.damages_gross_labourprod_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.labourprod_constant"
    )
    m.damages_gross_labourprod_temp_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.labourprod_temp_linear"
    )

    constraints.append(
        RegionalEquation(m.damage_costs_gross_labourprod, gross_dmg_fct_labourprod)
    )

    ## Adaptation (for now global costs, but should be regional in the future):
    m.adaptation_costs_abs_labourprod = Var(m.t, units=quant.unit("currency_unit"))
    m.adaptation_costs_labourprod = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.avoided_damages_adapt_labourprod = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.damage_costs_residual_labourprod = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.damage_costs_labourprod = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    # Parameters are now hardcoded, but should be regionalised:
    m.adaptation_labourprod_max_effectiveness = Param(initialize=0.33624)
    m.adaptation_labourprod_cost_param = Param(initialize=3.9144517)

    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.avoided_damages_adapt_labourprod,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.adaptation_costs_abs_labourprod[t],
                    m.adaptation_labourprod_max_effectiveness,
                    m.adaptation_labourprod_cost_param,
                ),
            ),
            # Adaptation costs as a fraction of GDP. Now every region gets same costs as % GDP
            RegionalEquation(
                m.adaptation_costs_labourprod,
                lambda m, t, r: m.adaptation_costs_abs_labourprod[t]
                / m.global_GDP_gross[t],
            ),
            # Residual damages after adaptation
            RegionalEquation(
                m.damage_costs_residual_labourprod,
                lambda m, t, r: m.damage_costs_gross_labourprod[t, r]
                * (1 - m.avoided_damages_adapt_labourprod[t, r]),
            ),
            # Total damages after adaptation
            RegionalEquation(
                m.damage_costs_labourprod,
                lambda m, t, r: m.damage_costs_residual_labourprod[t, r]
                + m.adaptation_costs_labourprod[t, r],
            ),
        ]
    )

    return constraints


def gross_dmg_fct_labourprod(m, t, r):

    a = m.damages_gross_labourprod_constant[r]
    b = m.damages_gross_labourprod_temp_linear[r]

    def fct(temp):
        return a + b * temp

    return fct(m.temperature[t]) - fct(m.temperature[0])
