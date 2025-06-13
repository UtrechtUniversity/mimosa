"""
Model equations and constraints:
Sea level rise (height of sea level rise, not SLR damages)
From RICE 2010
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
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    The sea-level rise (SLR) module is based on the AD-RICE 2012 model ([Kelly de Bruin, 2014](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2600006)),
    which in itself is based on RICE 2010. It consists of sea-level rise contributions from thermal expansion, glaciers and small ice caps (GSIC),
    and the Greenland ice sheet (GIS). Sea-level rise from Antarctica is not included due to the high uncertainty involved.

    # Thermal expansion

    :::mimosa.components.sealevelrise.slr_thermal_expansion
        options:
            show_source: false

    The initial sea-level rise due to thermal expansion (at time $t=0$) is calculated as:

    :::mimosa.components.sealevelrise.slr_thermal_expansion_init
        options:
            show_source: false


    with the following parameters:

    | Name | Description | Value |
    | --- | --- | --- |
    | $a$ | Adjustment rate for thermal expansion | 0.024076 |
    | $\\text{equil. rate}_{\\text{thermal}}$ | Equilibrium rate for thermal expansion | 0.5 m / °C  |
    | $\\text{SLR}_{\\text{thermal,init}}$ | Initial sea-level rise due to thermal expansion | 0.092067 m |



    # Glaciers and small ice caps (GSIC)

    :::mimosa.components.sealevelrise.slr_gsic
        options:
            show_source: false

    with as initial value:

    $$
    \\text{SLR}_{\\text{GSIC},0} = 0.015
    $$

    and with the following parameters:

    | Name | Description | Value |
    | --- | --- | --- |
    | $\\text{melt rate}$ | Melt rate | 0.0008 m / year |
    | $\\text{total ice}_{\\text{GSIC}}$ | Total ice | 0.26 m |
    | $\\text{equil. temp}_{\\text{GSIC}}$ | Equilibrium temperature | -1 °C |


    # Greenland ice sheet (GIS)

    :::mimosa.components.sealevelrise.slr_gis
        options:
            show_source: false

    with as initial value:

    $$
    \\text{SLR}_{\\text{GIS},0} = 0.006
    $$

    and with the following parameters:

    | Name | Description | Value |
    | --- | --- | --- |
    | $\\text{melt rate above thresh}$ | Melt rate above threshold | 1.1186 m / year |
    | $\\text{init melt rate}$ | Initial melt rate | 0.6 m / year |
    | $\\text{init ice volume}$ | Initial ice volume | 7.3 m |

    # Total sea-level rise

    The total sea-level rise is the sum of the contributions from thermal expansion, GSIC, and GIS:

    $$
    \\text{SLR}_t = \\text{SLR}_{\\text{thermal},t} + \\text{SLR}_{\\text{GSIC},t} + \\text{SLR}_{\\text{GIS},t}
    $$


    """

    # Parameters and variables necessary for sea level rise
    m.slr_thermal = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_thermal_equil = Param(initialize=0.5)  # Equilibrium
    m.slr_thermal_init = Param(
        initialize=0.0920666936642
    )  # Initial SLR due to thermal expansion
    m.slr_thermal_adjust_rate = Param(initialize=0.024076141150722)  # Adjustment rate

    m.slr_cumgsic = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_gsic_melt_rate = Param(initialize=0.0008)  # Melt rate
    m.slr_gsic_total_ice = Param(initialize=0.26)  # Total ice
    m.slr_gsic_equil_temp = Param(initialize=-1)  # Equilibrium temperature

    m.slr_cumgis = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_gis_melt_rate_above_thresh = Param(
        initialize=1.11860082
    )  # Melt rate above threshold
    m.slr_gis_init_melt_rate = Param(initialize=0.6)  # Initial melt rate
    m.slr_gis_init_ice_vol = Param(initialize=7.3)  # Initial ice volume

    m.total_SLR = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))

    # Constraints relating to SLR
    constraints = [
        # Thermal expansion
        GlobalEquation(
            m.slr_thermal,
            lambda m, t: (
                slr_thermal_expansion(m.slr_thermal[t - 1], m.temperature[t - 1], m)
                if t > 0
                else slr_thermal_expansion_init(m)
            ),
        ),
        # GSIC
        GlobalEquation(
            m.slr_cumgsic,
            lambda m, t: (
                slr_gsic(m.slr_cumgsic[t - 1], m.temperature[t - 1], m)
                if t > 0
                else 0.015
            ),
        ),
        # GIS
        GlobalEquation(
            m.slr_cumgis,
            lambda m, t: (
                slr_gis(m.slr_cumgis[t - 1], m.temperature[t - 1], m)
                if t > 0
                else 0.006
            ),
        ),
        # Total SLR is sum of each contributing factors
        GlobalEquation(
            m.total_SLR,
            lambda m, t: (m.slr_thermal[t] + m.slr_cumgsic[t] + m.slr_cumgis[t]),
        ),
    ]

    return constraints


def slr_thermal_expansion_init(m):
    """
    $$
    \\text{SLR}_{\\text{thermal},0} = \\text{SLR}_{\\text{thermal,init}} + a \\cdot (\\text{temperature}_{t=0} \\cdot \\text{equil. rate}_{\\text{thermal}} - \\text{SLR}_{\\text{thermal,init}})
    $$
    """
    return m.slr_thermal_init + m.slr_thermal_adjust_rate * (
        m.T0 * m.slr_thermal_equil - m.slr_thermal_init
    )


def slr_thermal_expansion(slr_thermal, temperature, m: AbstractModel):
    """
    The sea-level rise due to thermal expansion is calculated as follows:

    $$
    \\text{SLR}_{\\text{thermal}, t} = \\text{SLR}_{\\text{thermal},t-1} \\cdot (1 - a)^{\\frac{\\Delta t}{10}} + \\text{temperature}_{t-1} \\cdot a \\cdot \\tfrac{\\Delta t}{10} \\cdot \\text{equil. rate}_{\\text{thermal}}
    $$
    """

    equilib = m.slr_thermal_equil
    adjust_rate = m.slr_thermal_adjust_rate

    return (1 - adjust_rate) ** (m.dt / 10) * slr_thermal + adjust_rate * (
        m.dt / 10
    ) * (temperature * equilib)


def slr_gsic(cumgsic, temperature, m: AbstractModel):
    """
    Next, melting of glaciers and small ice caps (GSIC) contribute to sea-level rise according to:

    $$
    \\begin{align*}
    \\text{SLR}_{\\text{GSIC}, t} &= \\text{ SLR}_{\\text{GSIC}, t-1}\\\\
    +\\ &\\text{melt rate}\\cdot \\Delta t  \\cdot \\frac{\\text{total ice}_{\\text{GSIC}} - \\text{SLR}_{\\text{GSIC}, t-1}}{\\text{total ice}_{\\text{GSIC}}} \\cdot (\\text{temperature}_{t-1} - \\text{equil. temp}_{\\text{GSIC}})
    \\end{align*}
    $$
    """

    melt_rate = m.slr_gsic_melt_rate
    total_ice = m.slr_gsic_total_ice
    equil_temp = m.slr_gsic_equil_temp

    return cumgsic + melt_rate / total_ice * m.dt * (total_ice - cumgsic) * (
        temperature - equil_temp
    )


def slr_gis(cumgis, temperature, m: AbstractModel):
    """
    
    The Greenland ice sheet (GIS) contributes to sea-level rise according to:

    $$
    \\begin{align*}
    \\text{SLR}_{\\text{GIS}, t} &= \\text{SLR}_{\\text{GIS}, t-1}\\\\
    +\\ &\\tfrac{\\Delta t}{10} \\cdot \\tfrac{1}{100} \\cdot (\\text{melt rate above thresh} \\cdot \\text{temperature}_{t-1} + \\text{init melt rate}) \\\\
    & \\cdot \\left(1 - \\frac{\\text{SLR}_{\\text{GIS}, t-1}}{\\text{init ice volume}}\\right)
    \\end{align*}
    $$

    """

    melt_rate_above_thresh = m.slr_gis_melt_rate_above_thresh
    init_melt_rate = m.slr_gis_init_melt_rate
    init_ice_vol = m.slr_gis_init_ice_vol

    return cumgis + (m.dt / 10) * (1 / 100) * (
        melt_rate_above_thresh * temperature + init_melt_rate
    ) * (1 - cumgis / init_ice_vol)
