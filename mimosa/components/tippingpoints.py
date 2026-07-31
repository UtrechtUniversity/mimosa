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
    soft_max,
    soft_min,
    soft_switch,
    value,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """Comments"""

    constraints = []

    # total temperature anomaly due solely to crossing tipping points
    # temperature anomaly above PIA from increasing GHGs is NOT included in this value
    m.total_tipping_anomaly = Var(m.t, units=quant.unit("degC_above_PI"))

    # temperature anomalies accrued by crossing LABC threshold
    m.tipping_temps_LABC = Var(m.t, units=quant.unit("degC_above_PI"))
    # temperature anomalies accrued for each year by crossing PFAT threshold

    include_PFAT = context.option("tippingpoints", "include_PFAT")

    if include_PFAT:
        # ALl the PFAT stuff
        constraints.extend(get_PFAT_constraints(m))
    else:
        m.tipping_temps_PFAT = Param(
            m.t, units=quant.unit("degC_above_PI"), initialize=0.0
        )

    # temperature anomalies accrued for each year by crossing AMOC threshold
    m.tipping_temps_AMOC = Var(m.t, units=quant.unit("degC_above_PI"))
    # temperature anomalies accrued for each year by crossing AMAZ threshold
    m.tipping_temps_AMAZ = Var(m.t, units=quant.unit("degC_above_PI"))

    # temperature tipping threshold quantile for Labrador Sea convection collapse
    # taken from Anderson McKay (2022)
    # user can specify a value of 0.05, 0.5, or 0.95
    m.include_LABC = Param(doc="::tippingpoints.LABC.include")
    m.LABC_threshold_quantile = Param(doc="::tippingpoints.LABC.threshold_quantile")

    # temperature tipping threshold quantile for AMOC collapse
    # taken from Anderson McKay (2022)
    # user can specify a value of 0.05, 0.5, or 0.95
    m.include_AMOC = Param(doc="::tippingpoints.AMOC.include")
    m.AMOC_threshold_quantile = Param(doc="::tippingpoints.AMOC.threshold_quantile")

    # temperature tipping threshold quantile for AMAZ dieback carbon release
    m.include_AMAZ = Param(doc="::tippingpoints.AMAZ.include")
    m.AMAZ_threshold_quantile = Param(doc="::tippingpoints.AMAZ.threshold_quantile")
    m.AMAZ_severity_quantile = Param(doc="::tippingpoints.AMAZ.severity_quantile")

    #####################################################
    constraints.extend(
        [
            # PFAT global temperature anomaly
            # LABC global temperature anomaly
            GlobalEquation(
                m.tipping_temps_LABC,
                lambda m, t: (
                    (
                        calc_global_temp_LABC(
                            m.include_LABC,
                            m.LABC_threshold_quantile,
                            m.temperature[t],
                            m,
                        )
                    )
                    if t > 0
                    else 0
                ),
            ),
            # AMOC global temperature anomaly
            GlobalEquation(
                m.tipping_temps_AMOC,
                lambda m, t: (
                    (
                        calc_global_temp_AMOC(
                            m.include_AMOC,
                            m.AMOC_threshold_quantile,
                            m.temperature[t],
                            m,
                        )
                    )
                    if t > 0
                    else 0
                ),
            ),
            # AMAZ global temperature anomaly
            GlobalEquation(
                m.tipping_temps_AMAZ,
                lambda m, t: (
                    (
                        calc_global_temp_AMAZ(
                            m.include_AMAZ,
                            m.AMAZ_threshold_quantile,
                            m.temperature[t],
                            m.AMAZ_severity_quantile,
                            m,
                        )
                    )
                    if t > 0
                    else 0
                ),
            ),
            # total temperature anomaly from tipping is combination of all individual contributions
            GlobalEquation(
                m.total_tipping_anomaly,
                lambda m, t: (
                    m.tipping_temps_PFAT[t]
                    + m.tipping_temps_LABC[t]
                    + m.tipping_temps_AMOC[t]
                    + m.tipping_temps_AMAZ[t]
                ),
            ),
        ]
    )

    return constraints


def get_PFAT_constraints(m: AbstractModel):
    m.tipping_temps_PFAT = Var(m.t, units=quant.unit("degC_above_PI"))
    # temperature tipping threshold quantile for abrupt boreal permafrost thaw
    # taken from Anderson McKay (2022)
    # user can specify a value of 0.05, 0.5, or 0.95
    # m.include_PFAT = Param(doc="::tippingpoints.PFAT.include")
    m.PFAT_threshold_quantile = Param(doc="::tippingpoints.PFAT.threshold_quantile")
    # degree of severity quantile for the effects of crossing the PFAT tipping threshold
    # user can specify value as 0.05, 0.5, or 0.95 (from confidence interval)
    m.PFAT_severity_quantile = Param(doc="::tippingpoints.PFAT.severity_quantile")

    constraints = [
        GlobalEquation(
            m.tipping_temps_PFAT,
            lambda m, t: (
                calc_global_temp_PFAT(
                    m.include_PFAT,
                    m.PFAT_threshold_quantile,
                    m.temperature[t],
                    m.PFAT_severity_quantile,
                    m,
                )
                if t > 0
                else 0
            ),
        ),
    ]

    return constraints


###############################
# calculates the temperature anomaly from exceeding the PFAT tipping threshold
# uses estimate of 13 - 25 GtC released per degree Celsius over threshold (Anderson McKay 2022)
# this function uses the user-specified severity to determine which value to use
def calc_global_temp_PFAT(
    include_PFAT,
    PFAT_threshold_quantile,
    temp_current,
    PFAT_severity_quantile,
    m: AbstractModel,
):

    # if PFAT is set to False, don't do anything
    # TODO: This doesn't work...Too bad!
    if not value(include_PFAT):
        return 0

    else:

        # we initialize the severity to be 19 GtC per deg C, the 50th percentile value
        severity = 19.0
        # if user has selected 5th percentile, severity is set to 13 GtC
        if PFAT_severity_quantile == 0.05:
            severity = 13.0
        # if user has selected 95th percentile, severity is set to 25 GtC
        elif PFAT_severity_quantile == 0.95:
            severity = 25.0
        # if any other value is entered, set severity to median by default
        else:
            # TODO: Throw error
            severity = 19.0

        # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
        # the default value is the tipping threshold corresponding to 50th percentile
        threshold = 1.5
        # if user has selected 5th percentile, threshold is set to 1.0 deg C
        if PFAT_threshold_quantile == 0.05:
            threshold = 1.0
        # if user has selected 95th percentile, threshold is set to 2.3 deg C
        elif PFAT_threshold_quantile == 0.95:
            threshold = 2.3
        # if any other value is entered, set threshold to median by default
        else:
            # TODO: Throw error
            threshold = 1.5

        # conversion factor to convert GtC to GtCO2 (molecular weight of CO2 / molecular weight of C)
        conversion_factor = 44.0 / 12.0

        # temperature increase above PFAT threshold multiplied by GtC per degree C increase
        # this is then multiplied by a conversion factor to get GtCO2
        # multiplied by TCRE to get units of degrees C
        temp_total = (
            soft_switch(temp_current - threshold)
            * severity
            * conversion_factor
            * m.TCRE
        )
        return temp_total


###############################
# calculates the temperature anomaly from exceeding the LABC tipping threshold
# uses estimate of 0.46 degrees C of global cooling (Anderson McKay 2022)
# TODO: The change in GMST is currently represented as being proportional to the amount by which
#       the tipping temperature LABC_threshold has been exceeded.
#       This is NOT accurate...Too bad!
def calc_global_temp_LABC(
    include_LABC, LABC_threshold_quantile, temp_current, m: AbstractModel
):

    # if LABC is set to False, don't do anything
    # TODO: It still does something...Too bad!
    if value(include_LABC) == False:
        return 0

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    # default value is temperature corresponding to 50th percentile
    threshold = 1.8
    if LABC_threshold_quantile == 0.05:
        threshold = 1.1
    elif LABC_threshold_quantile == 0.95:
        threshold = 3.8
    else:
        # TODO: Throw error
        threshold = 1.8

    temp_total = -1.0 * (soft_switch(temp_current - threshold) * 0.46)
    return temp_total


###############################
# calculates the temperature anomaly from exceeding the AMOC tipping threshold
# uses estimate of 0.54 degrees C of global cooling (Anderson McKay 2022)
def calc_global_temp_AMOC(
    include_AMOC, AMOC_threshold_quantile, temp_current, m: AbstractModel
):

    # if AMOC is set to False, don't do anything
    # TODO: It still does something...Too bad!
    if value(include_AMOC) == False:
        return 0

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    # default value is temperature corresponding to 50th percentile
    threshold = 4.0
    if AMOC_threshold_quantile == 0.05:
        threshold = 1.4
    elif AMOC_threshold_quantile == 0.95:
        threshold = 8.0
    else:
        # TODO: Throw error
        threshold = 4.0

    temp_total = -1.0 * (soft_switch(temp_current - threshold) * 0.54)
    return temp_total


###############################
# calculates the temperature anomaly from exceeding the AMAZ tipping threshold
# uses estimate of 30-75 GtC (Anderson McKay 2022)
# TODO: only valid to 2100, use other numbers for up to 2300
def calc_global_temp_AMAZ(
    include_AMAZ,
    AMAZ_threshold_quantile,
    temp_current,
    AMAZ_severity_quantile,
    m: AbstractModel,
):

    # if AMAZ is set to False, don't do anything
    # TODO: It still does something...Too bad!
    if value(include_AMAZ) == False:
        return 0

    severity = 52.5
    if AMAZ_severity_quantile == 0.05:
        severity = 30.0
    elif AMAZ_severity_quantile == 0.95:
        severity = 75.0
    else:
        # TODO: Throw error
        severity = 52.5

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    threshold = 3.5
    if AMAZ_threshold_quantile == 0.05:
        threshold = 2.0
    elif AMAZ_threshold_quantile == 0.95:
        threshold = 6.0
    else:
        # TODO: Throw error
        threshold = 3.5

    temp_total = soft_switch(temp_current - threshold) * severity * m.TCRE
    return temp_total
