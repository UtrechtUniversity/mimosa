"""
Model equations and constraints:
Tipping points
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalEquation,
    NonNegativeReals,
    quant,
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """Comments"""

    # temperature anomalies accrued by crossing LABC threshold
    m.tipping_temps_LABC = Var(m.t)
    # temperature anomalies accrued by crossing PFAT threshold
    m.tipping_temps_PFAT = Var(m.t)



    # temperature tipping threshold for Labrador convection collapse
    m.LABC_threshold = Param(initialize=1.8)
    # Boolean indicator of whether LABC element has tipped
    m.LABC_tipped = Param(initialize=False)
    # year in which tipping occurred; if tipping has not occurred, value is set to -1
    m.LABC_tip_year = Param(initialize=-1)
    # temperature in year that tipping occurred
    m.LABC_tip_year_temp = Param(initialize=-1)


    # temperature tipping threshold for abrupt boreal permafrost thaw
    m.PFAT_threshold = Param(initialize=1.5)
    m.PFAT_tipped = Param(initialize=False)
    m.PFAT_tip_year = Param(initialize=-1)
    m.PFAT_tip_year_temp = Param(initialize=-1)
    

   

    # total temperature anomaly due to crossing tipping points
    m.total_tipping_anomaly = Var(m.t)

    constraints = [
        # total temperature anomaly from tipping is summation of all individual contributions
        GlobalEquation(
            m.total_tipping_anomaly,
             lambda m, t: (m.tipping_temps_LABC[t] + m.tipping_temps_PFAT[t]),
        ),

    ]

    return constraints


def calc_temp_PFAT(tip_year, temperature, m: AbstractModel):
        # do stuff
        # 13 - 25 GtC per degree Celsius
    return 0
        


    
