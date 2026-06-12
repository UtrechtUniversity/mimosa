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

    m.labourprod_damage_costs_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.labourprod_damages_gross_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.labourprod_constant"
    )
    m.labourprod_damages_gross_temp_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.labourprod_temp_linear"
    )

    constraints.append(
        RegionalEquation(m.labourprod_damage_costs_gross, gross_dmg_fct_labourprod)
    )

    ## Adaptation (for now global costs, but should be regional in the future):
    m.labourprod_adaptation_costs_abs = Var(m.t, units=quant.unit("currency_unit"))
    m.labourprod_adaptation_costs = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.labourprod_avoided_damages_adapt = Var(
        m.t, m.regions, units=quant.unit("fraction_of_gross_damages"), bounds=(0, 1)
    )
    m.labourprod_damage_costs_residual = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )
    m.labourprod_damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    # Parameters are now hardcoded, but should be regionalised:
    m.labourprod_adaptation_max_effectiveness = Param(initialize=0.33624)
    m.labourprod_adaptation_cost_param = Param(initialize=3.9144517)

    constraints.extend(
        [
            # Adaptation effectiveness function
            RegionalEquation(
                m.labourprod_avoided_damages_adapt,
                lambda m, t, r: adaptation_effectiveness_fct(
                    m.labourprod_adaptation_costs_abs[t],
                    m.labourprod_adaptation_max_effectiveness,
                    m.labourprod_adaptation_cost_param,
                ),
            ),
            # Adaptation costs as a fraction of GDP. Now every region gets same costs as % GDP
            RegionalEquation(
                m.labourprod_adaptation_costs,
                lambda m, t, r: m.labourprod_adaptation_costs_abs[t]
                / m.global_GDP_gross[t],
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
                + m.labourprod_adaptation_costs[t, r],
            ),
        ]
    )

    return constraints


def gross_dmg_fct_labourprod(m, t, r):

    a = m.labourprod_damages_gross_constant[r]
    b = m.labourprod_damages_gross_temp_linear[r]

    def fct(temp):
        return a + b * temp

    return fct(m.temperature[t]) - fct(m.temperature[0])
