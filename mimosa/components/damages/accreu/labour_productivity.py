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

    m.damage_costs_labourprod_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.damages_gross_labourprod_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.labourprod_constant"
    )

    m.damages_gross_labourprod_temp_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.labourprod_temp_linear"
    )

    constraints.append(
        RegionalEquation(m.damage_costs_labourprod_gross, gross_dmg_fct_labourprod)
    )

    return constraints


def gross_dmg_fct_labourprod(m, t, r):

    a = m.damages_gross_labourprod_constant[r]
    b = m.damages_gross_labourprod_temp_linear[r]

    def fct(temp):
        return a + b * temp

    return fct(m.temperature[t]) - fct(m.temperature[0])
