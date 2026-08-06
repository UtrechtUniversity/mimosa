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

    # total temperature anomaly due solely to effects of crossing tipping thresholds
    # temperature anomaly above PIA from increasing GHGs is NOT included in this value
    m.total_tipping_anomaly = Var(m.t, units=quant.unit("degC_above_PI"))

    # read in model structure specified by user to see which tipping elements should be included
    include_ALL = context.option("tipping points options", "include ALL")
    include_PFAT = context.option("tipping points options", "include PFAT")
    include_LABC = context.option("tipping points options", "include LABC")
    include_AMOC = context.option("tipping points options", "include AMOC")
    include_AMAZ = context.option("tipping points options", "include AMAZ")

    # if user specifies inclusion of PFAT tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_PFAT or include_ALL:
        # ALL the PFAT stuff
        constraints.extend(get_PFAT_constraints(m))
    else:
        m.tipping_temps_PFAT = Param(
            m.t, units=quant.unit("degC_above_PI"), initialize=0.0
        )

    # if user specifies inclusion of LABC tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_LABC or include_ALL:
            # ALL the LABC stuff
            constraints.extend(get_LABC_constraints(m))
    else:
        m.tipping_temps_LABC = Param(
            m.t, units=quant.unit("degC_above_PI"), initialize=0.0
        )


    # if user specifies inclusion of AMOC tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_AMOC or include_ALL:
            # ALL the AMOC stuff
            constraints.extend(get_AMOC_constraints(m))
    else:
        m.tipping_temps_AMOC = Param(
            m.t, units=quant.unit("degC_above_PI"), initialize=0.0
        )


    # if user specifies inclusion of AMAZ tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_AMAZ or include_ALL:
            # ALL the AMAZ stuff
            constraints.extend(get_AMAZ_constraints(m))
    else:
        m.tipping_temps_AMAZ = Param(
            m.t, units=quant.unit("degC_above_PI"), initialize=0.0
        )

    

    #####################################################
    constraints.extend(
        [
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
    # Var for additional GMST temperature anomaly due to PFAT tipping element
    m.tipping_temps_PFAT = Var(m.t, units=quant.unit("degC_above_PI"))
    # temperature tipping threshold quantile for PFAT tipping element
    # user can specify a value of 0.05, 0.5, or 0.95
    m.PFAT_threshold_quantile = Param(doc="::tippingpoints.PFAT.threshold_quantile")
    # degree of severity quantile for the effects of crossing the PFAT tipping threshold
    # user can specify value as 0.05, 0.5, or 0.95 (from confidence interval)
    m.PFAT_severity_quantile = Param(doc="::tippingpoints.PFAT.severity_quantile")

    constraints = [
        GlobalEquation(
            m.tipping_temps_PFAT,
            lambda m, t: (
                calc_global_temp_PFAT(
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



def get_LABC_constraints(m: AbstractModel):
    # Var for additional GMST temperature anomaly due to LABC tipping element
    m.tipping_temps_LABC = Var(m.t, units=quant.unit("degC_above_PI"))
    m.LABC_threshold_quantile = Param(doc="::tippingpoints.LABC.threshold_quantile")

    constraints = [
            GlobalEquation(
                m.tipping_temps_LABC,
                lambda m, t: (
                    calc_global_temp_LABC(
                        m.LABC_threshold_quantile,
                        m.temperature[t],
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),
        ]

    return constraints



def get_AMOC_constraints(m: AbstractModel):
    # Var for additional GMST temperature anomaly due to AMOC tipping element
    m.tipping_temps_AMOC = Var(m.t, units=quant.unit("degC_above_PI"))
    m.AMOC_threshold_quantile = Param(doc="::tippingpoints.AMOC.threshold_quantile")

    constraints = [
            GlobalEquation(
                m.tipping_temps_AMOC,
                lambda m, t: (
                    calc_global_temp_AMOC(
                        m.AMOC_threshold_quantile,
                        m.temperature[t],
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),
        ]

    return constraints



def get_AMAZ_constraints(m: AbstractModel):
    # Var for additional GMST temperature anomaly due to AMAZ tipping element
    m.tipping_temps_AMAZ = Var(m.t, units=quant.unit("degC_above_PI"))
    m.AMAZ_threshold_quantile = Param(doc="::tippingpoints.AMAZ.threshold_quantile")
    m.AMAZ_severity_quantile = Param(doc="::tippingpoints.AMAZ.severity_quantile")

    constraints = [
            GlobalEquation(
                m.tipping_temps_AMAZ,
                lambda m, t: (
                    calc_global_temp_AMAZ(
                        m.AMAZ_threshold_quantile,
                        m.temperature[t],
                        m.AMAZ_severity_quantile,
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
    PFAT_threshold_quantile,
    temp_current,
    PFAT_severity_quantile,
    m: AbstractModel,
):

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
        # TODO: remove severity = 19.0 once we figure out how to throw an error
        severity = 19.0

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    # the default value is the tipping threshold corresponding to the 50th percentile
    threshold = 1.5
    # if user has selected 5th percentile, threshold is set to 1.0 deg C
    if PFAT_threshold_quantile == 0.05:
        threshold = 1.0
    # if user has selected 95th percentile, threshold is set to 2.3 deg C
    elif PFAT_threshold_quantile == 0.95:
        threshold = 2.3
    # if any other value is entered, throw error
    else:
        # TODO: Throw error
        # TODO: remove threshold = 1.5 once we figure out how to throw an error
        threshold = 1.5

    # conversion factor to convert GtC to GtCO2 (molecular weight of CO2 / molecular weight of C)
    conversion_factor = 44.0 / 12.0

    # temperature increase above PFAT threshold multiplied by GtC per degree C increase
    # this is then multiplied by a conversion factor to get GtCO2
    # multiplied by TCRE to get units of degrees C
    temp_total = (soft_switch(temp_current - threshold) * severity * conversion_factor * m.TCRE)

    return temp_total


###############################
# calculates the temperature anomaly from exceeding the LABC tipping threshold
# uses estimate of 0.46 degrees C of global cooling (Anderson McKay 2022)
# TODO: The change in GMST is currently represented as being proportional to the amount by which
#       the tipping temperature LABC_threshold has been exceeded.
#       This is NOT accurate...Too bad!
def calc_global_temp_LABC(
    LABC_threshold_quantile, temp_current, m: AbstractModel
):

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    # default value is temperature corresponding to 50th percentile
    threshold = 1.8
    if LABC_threshold_quantile == 0.05:
        threshold = 1.1
    elif LABC_threshold_quantile == 0.95:
        threshold = 3.8
    else:
        # TODO: Throw error
        # TODO: Remove threshold value after figuring out how to throw error
        threshold = 1.8

    # temperature anomaly is multiplied by -1.0 because LABC leads to global cooling
    temp_total = -1.0 * (soft_switch(temp_current - threshold) * 0.46)
    return temp_total


###############################
# calculates the temperature anomaly from exceeding the AMOC tipping threshold
# uses estimate of 0.54 degrees C of global cooling (Anderson McKay 2022)
def calc_global_temp_AMOC(
    AMOC_threshold_quantile, temp_current, m: AbstractModel
):

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    # default value is temperature corresponding to 50th percentile
    threshold = 4.0
    if AMOC_threshold_quantile == 0.05:
        threshold = 1.4
    elif AMOC_threshold_quantile == 0.95:
        threshold = 8.0
    else:
        # TODO: Throw error
        # TODO: Remove threshold value after figuring out how to throw error
        threshold = 4.0

    # temperature anomaly is multiplied by -1.0 because AMOC leads to global cooling
    temp_total = -1.0 * (soft_switch(temp_current - threshold) * 0.54)
    return temp_total


###############################
# calculates the temperature anomaly from exceeding the AMAZ tipping threshold
# uses estimate of 30-75 GtC (Anderson McKay 2022)
# TODO: only valid to 2100, use other numbers for up to 2300
def calc_global_temp_AMAZ(
    AMAZ_threshold_quantile,
    temp_current,
    AMAZ_severity_quantile,
    m: AbstractModel,
):

    severity = 52.5
    if AMAZ_severity_quantile == 0.05:
        severity = 30.0
    elif AMAZ_severity_quantile == 0.95:
        severity = 75.0
    else:
        # TODO: Throw error
        # TODO: Remove severity setting after figuring out how to throw error
        severity = 52.5

    # setting temperature threshold at which tipping occurs from Anderson McKay confidence interval
    threshold = 3.5
    if AMAZ_threshold_quantile == 0.05:
        threshold = 2.0
    elif AMAZ_threshold_quantile == 0.95:
        threshold = 6.0
    else:
        # TODO: Throw error
        # TODO: Remove threshold setting after figuring out how to throw error
        threshold = 3.5

    temp_total = soft_switch(temp_current - threshold) * severity * m.TCRE
    return temp_total
