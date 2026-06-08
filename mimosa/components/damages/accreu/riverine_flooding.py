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

    m.damage_costs_riverine_gross = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    m.damages_gross_riverine_constant = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_constant"
    )
    m.damages_gross_riverine_time_div_100_linear = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_time_div_100_linear"
    )
    m.damages_gross_riverine_time_div_100_squared = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_time_div_100_squared"
    )
    m.damages_gross_riverine_temp_squared = Param(
        m.regions, doc="regional::ACCREU_sectoral.riverine_temp_squared"
    )

    constraints.append(
        RegionalEquation(m.damage_costs_riverine_gross, gross_dmg_fct_riverine)
    )

    return constraints


def gross_dmg_fct_riverine(m, t, r):

    a = m.damages_gross_riverine_constant[r]
    b = m.damages_gross_riverine_time_div_100_linear[r]
    c = m.damages_gross_riverine_time_div_100_squared[r]
    d = m.damages_gross_riverine_temp_squared[r]

    def fct(time, temp):
        return a + b * (time / 100) + c * (time / 100) ** 2 + d * temp**2

    return fct(m.year(t) - 2020, m.temperature[t]) - fct(0, m.temperature[0])
