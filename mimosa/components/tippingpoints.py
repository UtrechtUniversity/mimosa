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
    include_ALL = context.option("tippingpoints", "include ALL")
    include_PFAT = context.option("tippingpoints", "include PFAT")
    include_LABC = context.option("tippingpoints", "include LABC")
    include_AMOC = context.option("tippingpoints", "include AMOC")
    include_AMAZ = context.option("tippingpoints", "include AMAZ")
    include_AWSI = context.option("tippingpoints", "include AWSI")

    # if user specifies inclusion of AMAZ tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_AMAZ or include_ALL:
            # ALL the AMAZ stuff
            constraints.extend(get_AMAZ_constraints(m))
    else:
        m.tipping_temps_AMAZ = Param(
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


    # if user specifies inclusion of AWSI tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_AWSI or include_ALL:
            # ALL the AWSI stuff
            constraints.extend(get_AWSI_constraints(m))
    else:
        m.tipping_temps_AWSI = Param(
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


    # if user specifies inclusion of PFAT tipping element in model structure
    # OR if user specifies including of ALL tipping elements in model structure
    if include_PFAT or include_ALL:
        # ALL the PFAT stuff
        constraints.extend(get_PFAT_constraints(m))
    else:
        m.tipping_temps_PFAT = Param(
            m.t, units=quant.unit("degC_above_PI"), initialize=0.0
        )



    #####################################################
    constraints.extend(
        [
            # total temperature anomaly from tipping is combination of all individual contributions
            GlobalEquation(
                m.total_tipping_anomaly,
                lambda m, t: (
                    m.tipping_temps_AMAZ[t]
                    + m.tipping_temps_AMOC[t]
                    + m.tipping_temps_AWSI[t]
                    + m.tipping_temps_LABC[t]
                    + m.tipping_temps_PFAT[t]
                ),
            ),
        ]
    )

    return constraints



def get_AMAZ_constraints(m: AbstractModel):
    # variable for additional GMST temperature anomaly due to AMAZ tipping element
    m.tipping_temps_AMAZ = Var(m.t, units=quant.unit("degC_above_PI"))
    # variable to store whether temperature at current timestep exceeds tipping threshold
    m.tipped_AMAZ = Var(m.t)
    # variable to store whether threshold has been crossed at any previous timestep
    m.tipped_state_AMAZ = Var(m.t)
    m.AMAZ_severity_quantile = Param(doc="::tippingpoints.AMAZ.severity_quantile")
    m.AMAZ_threshold = Param(doc="::tippingpoints.AMAZ.threshold")
    

    constraints = [
            GlobalEquation(
                m.tipping_temps_AMAZ,
                lambda m, t: (
                    calc_global_temp_AMAZ(
                        m.temperature[t-1],
                        m.tipped_state_AMAZ[t-1],
                        m.AMAZ_severity_quantile,
                        m.AMAZ_threshold,
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_AMAZ,
                lambda m, t: (
                    check_tipped_AMAZ(
                        m.temperature[t-1],
                        m.AMAZ_threshold,
                        m,
                    )
                    if t > 0
                    else 0 
                ),
            ),

            GlobalEquation(
                m.tipped_state_AMAZ,
                lambda m, t: (
                    check_tipped_state_AMAZ(
                        m.tipped_AMAZ[t-1],
                        m.tipped_state_AMAZ[t-1],
                        m,
                    )
                    if t > 0
                    else 0  
                ),
            ),
        ]

    return constraints



def get_AMOC_constraints(m: AbstractModel):
    # variable for additional GMST temperature anomaly due to AMOC tipping element
    m.tipping_temps_AMOC = Var(m.t, units=quant.unit("degC_above_PI"))
    # variable to store whether temperature at current timestep exceeds tipping threshold
    m.tipped_AMOC = Var(m.t)
    # variable to store whether threshold has been crossed at any previous timestep 
    m.tipped_state_AMOC = Var(m.t)
    m.AMOC_threshold = Param(doc="::tippingpoints.AMOC.threshold")
    

    constraints = [
            GlobalEquation(
                m.tipping_temps_AMOC,
                lambda m, t: (
                    calc_global_temp_AMOC(
                        m.temperature[t-1],
                        m.tipped_state_AMOC[t-1],
                        m.AMOC_threshold,
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_AMOC,
                lambda m, t: (
                    check_tipped_AMOC(
                        m.temperature[t-1],
                        m.AMOC_threshold,
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_state_AMOC,
                lambda m, t: (
                    check_tipped_state_AMOC(
                        m.tipped_AMOC[t-1],
                        m.tipped_state_AMOC[t-1],
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),
        ]

    return constraints



def get_AWSI_constraints(m: AbstractModel):
    # variable for additional GMST temperature anomaly due to AWSI tipping element
    m.tipping_temps_AWSI = Var(m.t, units=quant.unit("degC_above_PI"))
    # variable to store whether temperature at current timestep exceeds tipping threshold
    m.tipped_AWSI = Var(m.t)
    # variable to store whether threshold has been crossed at any previous timestep
    m.tipped_state_AWSI = Var(m.t)
    m.AWSI_threshold = Param(doc="::tippingpoints.AWSI.threshold")
    

    constraints = [
            GlobalEquation(
                m.tipping_temps_AWSI,
                lambda m, t: (
                    calc_global_temp_AWSI(
                        m.temperature[t-1],
                        m.tipped_state_AWSI[t-1],
                        m.AWSI_threshold,
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_AWSI,
                lambda m, t: (
                    check_tipped_AWSI(
                        m.temperature[t-1],
                        m.AWSI_threshold,
                        m,
                    )  
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_state_AWSI,
                lambda m, t: (
                    check_tipped_state_AWSI(
                        m.tipped_AWSI[t-1],
                        m.tipped_state_AWSI[t-1],
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),
        ]

    return constraints



def get_LABC_constraints(m: AbstractModel):
    # variable for additional GMST temperature anomaly due to LABC tipping element
    m.tipping_temps_LABC = Var(m.t, units=quant.unit("degC_above_PI"))
    # variable to store whether temperature at current timestep exceeds tipping threshold
    m.tipped_LABC = Var(m.t)
    # variable to store whether threshold has been crossed at any previous timestep
    m.tipped_state_LABC = Var(m.t)
    m.LABC_threshold = Param(doc="::tippingpoints.LABC.threshold")
    

    constraints = [
            GlobalEquation(
                m.tipping_temps_LABC,
                lambda m, t: (
                    calc_global_temp_LABC(
                        m.temperature[t-1],
                        m.tipped_state_LABC[t-1],
                        m.LABC_threshold,
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_LABC,
                lambda m, t: (
                    check_tipped_LABC(
                        m.temperature[t-1],
                        m.LABC_threshold,
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),

            GlobalEquation(
                m.tipped_state_LABC,
                lambda m, t: (
                    check_tipped_state_LABC(
                        m.tipped_LABC[t-1],
                        m.tipped_state_LABC[t-1],
                        m,
                    )
                    if t > 0
                    else 0
                ),
            ),
        ]

    return constraints



def get_PFAT_constraints(m: AbstractModel):
    # variable for additional GMST temperature anomaly due to PFAT tipping element
    m.tipping_temps_PFAT = Var(m.t, units=quant.unit("degC_above_PI"))
    # variable to store whether temperature at current timestep exceeds tipping threshold
    m.tipped_PFAT = Var(m.t)
    # variable to store whether threshold has been crossed at any previous timestep
    m.tipped_state_PFAT = Var(m.t)
    # degree of severity quantile for the effects of crossing the PFAT tipping threshold
    # user can specify value as 0.05, 0.5, or 0.95 (from confidence interval)
    m.PFAT_severity_quantile = Param(doc="::tippingpoints.PFAT.severity_quantile")
    # temperature to use as tipping threshold
    m.PFAT_threshold = Param(doc="::tippingpoints.PFAT.threshold")

    constraints = [
        GlobalEquation(
            m.tipping_temps_PFAT,
            lambda m, t: (
                calc_global_temp_PFAT(
                    m.temperature[t-1],
                    m.tipped_state_PFAT[t-1],
                    m.PFAT_severity_quantile,
                    m.PFAT_threshold,
                    m.year(t),
                    m,
                )
                if t > 0
                else 0
            ),
        ),

        GlobalEquation(
            m.tipped_PFAT,
            lambda m, t: (
                check_tipped_PFAT(
                    m.temperature[t-1],
                    m.PFAT_threshold,
                    m,
                )
                if t > 0
                else 0
            ),
        ),

        GlobalEquation(
            m.tipped_state_PFAT,
            lambda m, t: (
                check_tipped_state_PFAT(
                    m.tipped_PFAT[t-1],
                    m.tipped_state_PFAT[t-1],
                    m,
                )
                if t > 0
                else 0
            ),
        ),
    ]

    return constraints



###############################
# determines whether current temperature exceeds the tipping threshold
def check_tipped_AMAZ(temp_current, threshold, m: AbstractModel,):

    tipped_new = soft_switch(temp_current - threshold)

    return tipped_new


###############################
# determines whether the temperature at any previous timestep has exceeded the tipping threshold
def check_tipped_state_AMAZ(tipped, tipped_state_current, m: AbstractModel,):

     tipped_state_new = tipped_state_current + (1 - tipped_state_current)*tipped

     return tipped_state_new



###############################
# calculates the temperature anomaly from exceeding the AMAZ tipping threshold
# uses estimate of 30-75 GtC (Anderson McKay 2022)
# TODO: only valid to 2100, use other numbers for up to 2300
# TODO: Anderson McKay suggests that threshold temperature will likely be lower when accounting for
#       the effects of deforestation
def calc_global_temp_AMAZ(
    temp_current,
    tipped_state_current,
    AMAZ_severity_quantile,
    AMAZ_threshold,
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

    threshold = AMAZ_threshold

    # needed to convert from gigatons carbon to gigatons CO2
    CO2_conversion_factor = 44.0 / 12.0

    temp_total = tipped_state_current * CO2_conversion_factor * severity * m.TCRE

    return temp_total



###############################
# determines the tipping state for AMOC
def check_tipped_AMOC(temp_current, threshold, m: AbstractModel,):

    tipped_new = soft_switch(temp_current - threshold)

    return tipped_new


###############################
# determines whether the temperature at any previous timestep has exceeded the tipping threshold
def check_tipped_state_AMOC(tipped, tipped_state_current, m: AbstractModel,):

    tipped_state_new = tipped_state_current + (1 - tipped_state_current)*tipped

    return tipped_state_new


###############################
# calculates the temperature anomaly from exceeding the AMOC tipping threshold
# uses estimate of 0.54 degrees C of global cooling (Anderson McKay 2022)
def calc_global_temp_AMOC(
    temp_current, tipped_state_current, AMOC_threshold, m: AbstractModel,
):

    threshold = AMOC_threshold
    
    # temperature anomaly is multiplied by -1.0 because AMOC collapse leads to global cooling
    temp_total = -1.0 * (tipped_state_current * 0.54)
    
    return temp_total



###############################
# determines the tipping state for AWSI
def check_tipped_AWSI(temp_current, threshold, m: AbstractModel,):

    tipped_new = soft_switch(temp_current - threshold)

    return tipped_new


###############################
# determines whether the temperature at any previous timestep has exceeded the tipping threshold
def check_tipped_state_AWSI(tipped, tipped_state_current, m: AbstractModel,):

    tipped_state_new = tipped_state_current + (1 - tipped_state_current)*tipped

    return tipped_state_new



###############################
# calculates the global temperature anomaly from exceeding the AWSI tipping threshold
def calc_global_temp_AWSI(
    temp_current,
    tipped_state_current,
    AWSI_threshold,
    m: AbstractModel,
):

    threshold = AWSI_threshold

    temp_total = (tipped_state_current * 0.60)

    return temp_total



###############################
# determines the tipping state for LABC
def check_tipped_LABC(temp_current, threshold, m: AbstractModel,):

    tipped_new = soft_switch(temp_current - threshold)

    return tipped_new


###############################
# determines whether the temperature at any previous timestep has exceeded the tipping threshold
def check_tipped_state_LABC(tipped, tipped_state_current, m: AbstractModel,):

    tipped_state_new = tipped_state_current + (1 - tipped_state_current)*tipped

    return tipped_state_new



###############################
# calculates the temperature anomaly from exceeding the LABC tipping threshold
# uses estimate of 0.46 degrees C of global cooling in total (Anderson McKay 2022)
def calc_global_temp_LABC(
    temp_current, tipped_state_current, LABC_threshold, m: AbstractModel,
):

    threshold = LABC_threshold

    # temperature anomaly is multiplied by -1.0 because LABC leads to global cooling
    temp_total = -1.0 * (tipped_state_current * 0.46)

    return temp_total



###############################
# determines the tipping state for PFAT
def check_tipped_PFAT(temp_current, threshold, m: AbstractModel,):

    tipped_new = soft_switch(temp_current - threshold)

    return tipped_new



###############################
# determines whether the temperature at any previous timestep has exceeded the tipping threshold
def check_tipped_state_PFAT(tipped, tipped_state_current, m: AbstractModel,):

     tipped_state_new = tipped_state_current + (1 - tipped_state_current)*tipped

     return tipped_state_new


###############################
# calculates the global temperature anomaly from exceeding the PFAT tipping threshold
# uses estimates of carbon-equivalent release from Anderson-McKay (2022)
# severity quantile corresponds to the range of carbon-equivalent release values provided in this paper
def calc_global_temp_PFAT(
    temp_current,
    tipped_state_current,
    PFAT_severity_quantile,
    PFAT_threshold,
    year_current,
    m: AbstractModel,
):

    # we treat the range of carbon release values in Anderson-McKay as a 95% confidence interval
    # these values are valid up until the year 2100
    # units are GtC
    carbon_release = 10.5
    if (PFAT_severity_quantile == 0.05):
         carbon_release = 7.0
    elif (PFAT_severity_quantile == 0.95):
         carbon_release = 14.0

    # after the year 2100, we use the values for carbon release between 2100 and 2300
    # in order to simulate a gradual release (rather than a pulse emission) we create a linear function
    # based on the amount of temperature increase since 2100

    # variable to store the temperature at the year 2100
    temp_2100 = 0
    if (year_current == 2100):
         temp_2100 = temp_current
         
    # if the year is after 2100, calculate the carbon release using the post-2100 values
    # and in proportion to the amount by which the current temperature has exceeded the 2100 temperature
    if (year_current > 2100 and PFAT_severity_quantile == 0.5):
         carbon_release = 26.5 * (temp_current - temp_2100)
    elif (year_current > 2100 and PFAT_severity_quantile == 0.05):
         carbon_release = 18.0 * (temp_current - temp_2100)
    elif (year_current > 2100 and PFAT_severity_quantile == 0.95):
         carbon_release = 35.0 * (temp_current - temp_2100)

    
    # setting temperature threshold at which tipping occurs
    # this value is provided by the stochastic probability draw in run.py
    threshold = PFAT_threshold
    
    # conversion factor to convert carbon to CO2 (molecular weight of CO2 / molecular weight of C)
    CO2_conversion_factor = 44.0 / 12.0

    # temperature increase above PFAT threshold multiplied by amount of carbon release
    # this is then multiplied by a conversion factor to get value in terms of CO2
    # then multiplied by TCRE to get units of degrees C
    temp_total = (tipped_state_current * carbon_release * CO2_conversion_factor * m.TCRE) 

    return temp_total


