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

    # total temperature anomaly due to crossing tipping points
    m.total_tipping_anomaly = Var(m.t)
    # temperature anomalies accrued by crossing LABC threshold
    m.tipping_temps_LABC = Var(m.t)
    # temperature anomalies accrued by crossing PFAT threshold
    m.tipping_temps_PFAT = Var(m.t)

    # temperature tipping threshold for abrupt boreal permafrost thaw
    # taken from Anderson McKay (2022)
    m.PFAT_threshold = Param(initialize=1.5)
    # boolean to store whether or not tipping point has been crossed
    m.PFAT_tipped = Param(initialize=False)
    # year in which tipping point was crossed (needed for temperature anomaly calculation)
    m.PFAT_tip_year = Param(initialize=-1)
    # GMST in the year during which the tipping point was crossed
    m.PFAT_tip_year_temp = Param(initialize=-1)

    constraints = [
        # PFAT temperature anomaly
        GlobalEquation(
            m.tipping_temps_PFAT,
            lambda m, t: (
                calc_temp_PFAT(
                    m.PFAT_tipped,
                    m.PFAT_threshold,
                    m.PFAT_tip_year,
                    m.temperature[t],
                    m.temperature[t - 1],
                    m,
                )
                if t > 0
                else 0
            ),
        ),
        # total temperature anomaly from tipping is summation of all individual contributions
        GlobalEquation(
            m.total_tipping_anomaly,
            lambda m, t: (m.tipping_temps_LABC[t] + m.tipping_temps_PFAT[t]),
        ),
    ]

    return constraints


# calculates the temperature anomaly from exceeding the PFAT tipping threshold
# uses estimate of 13 - 25 GtC released per degree Celsius over threshold (Anderson McKay 2022)
# this function uses an average of 19 GtC released per degree C over tipping threshold
def calc_temp_PFAT(
    PFAT_tipped,
    PFAT_threshold,
    PFAT_tip_year,
    temp_current,
    temp_prev,
    m: AbstractModel,
):
    # if tipping threshold has not been crossed, return 0
    if PFAT_tipped == False:
        return 0
    # if it is NOT the first year for which we've passed the tipping threshold
    elif m.t > PFAT_tip_year:
        # the amount of new carbon released is equal to the temperature change from
        # the previous year to the current year multiplied by 19
        # !!! TODO: assumes m.temperature[t] is greater than m.temperature[t-1]
        new_carbon_released = (temp_current - temp_prev) * 19
        # temperature anomaly is amount of new carbon released times TCRE
        PFAT_temp_anomaly = new_carbon_released * m.TCRE
        return PFAT_temp_anomaly
    # if it IS the first year that we've passed the tipping threshold
    else:
        # for the first year past the tipping threshold, we compare current temperature
        # to the tipping threshold instead of the previous year's temperature
        new_carbon_released = (temp_current - PFAT_threshold) * 19
        PFAT_temp_anomaly = new_carbon_released * m.TCRE
        return PFAT_temp_anomaly


# checks to see if GMST has crossed the PFAT tipping threshold
# TODO: how do I add this into constraints?
def PFAT_tip_check(temp_current, PFAT_threshold, m: AbstractModel):
    if temp_current >= PFAT_threshold:
        m.PFAT_tipped = True
        m.PFAT_tip_year = m.t
    return 0
