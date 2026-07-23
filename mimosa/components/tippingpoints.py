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
from mimosa.common import soft_max, soft_min, soft_switch


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """Comments"""

    # total temperature anomaly due solely to crossing tipping points
    # temperature anomaly above PIA from increasing GHGs is NOT included in this value
    m.total_tipping_anomaly = Var(m.t, units=quant.unit("degC_above_PI"))
    # temperature anomalies accrued by crossing LABC threshold
    m.tipping_temps_LABC = Var(m.t, units=quant.unit("degC_above_PI"))
    # temperature anomalies accrued for each year by crossing PFAT threshold
    m.tipping_temps_PFAT = Var(m.t, units=quant.unit("degC_above_PI"))


    # temperature tipping threshold for abrupt boreal permafrost thaw
    # taken from Anderson McKay (2022)
    m.PFAT_threshold = Param(initialize=1.5)

 
    # temperature tipping threshold for Labrador Sea convection collapse
    # taken from Anderson McKay (2022)
    m.LABC_threshold = Param(initialize=1.8)



#####################################################
    constraints = [
        # PFAT global temperature anomaly
        GlobalEquation(
            m.tipping_temps_PFAT,
            lambda m, t: (
                calc_global_temp_PFAT(
                    m.PFAT_threshold,
                    m.temperature[t],
                    m,
                )
                if t > 0
                else 0
            ),
        ),

        # LABC global temperature anomaly
        GlobalEquation(
            m.tipping_temps_LABC,
            lambda m, t: (calc_global_temp_LABC(m.LABC_threshold, m.temperature[t], m,))
            if t > 0
            else 0
        ),


        # total temperature anomaly from tipping is combination of all individual contributions
        # warming temperature anomalies are added, cooling temperature anomalies are subtracted
        GlobalEquation(
            m.total_tipping_anomaly,
            lambda m, t: (m.tipping_temps_PFAT[t] - m.tipping_temps_LABC[t]),
        ),


    ]

    return constraints


# calculates the temperature anomaly from exceeding the PFAT tipping threshold
# uses estimate of 13 - 25 GtC released per degree Celsius over threshold (Anderson McKay 2022)
# this function uses an average of 19 GtC released per degree C over tipping threshold
def calc_global_temp_PFAT(
    PFAT_threshold,
    temp_current,
    m: AbstractModel,
):
    # temperature increase above PFAT threshold multiplied by 19 GtC per degree C increase
    # multiplied by TCRE to get units of degrees C
    temp_total = ( soft_switch(temp_current - PFAT_threshold) * 19 * m.TCRE)
    return temp_total
 

# calculates the temperature anomaly from exceeding the LABC tipping threshold
# uses estimate of 0.46 degrees C of global cooling (Anderson McKay 2022)
# TODO: The change in GMST is currently represented as being proportional to the amount by which
#       the tipping temperature LABC_threshold has been exceeded. This is NOT accurate.
def calc_global_temp_LABC(LABC_threshold, temp_current, m: AbstractModel):

    temp_total = ( soft_switch(temp_current - LABC_threshold) * 0.46)
    return temp_total
        
