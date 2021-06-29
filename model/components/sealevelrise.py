"""
Model equations and constraints:
Sea level rise (height of sea level rise, not SLR damages)
From RICE 2010
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    Constraint,
    NonNegativeReals,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emissions and temperature equations and constraints

    Necessary variables:
        m.total_SLR

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """

    # Parameters and variables necessary for sea level rise
    m.slr_thermal = Var(m.t, within=NonNegativeReals)
    m.slr_thermal_equil = Param()
    m.slr_thermal_init = Param()
    m.slr_thermal_adjust_rate = Param()

    m.slr_cumgsic = Var(m.t, within=NonNegativeReals)
    m.slr_gsic_melt_rate = Param()
    m.slr_gsic_total_ice = Param()
    m.slr_gsic_equil_temp = Param()

    m.slr_cumgis = Var(m.t, within=NonNegativeReals)
    m.slr_gis_melt_rate_above_thresh = Param()
    m.slr_gis_init_melt_rate = Param()
    m.slr_gis_init_ice_vol = Param()

    m.total_SLR = Var(m.t, within=NonNegativeReals)

    # Constraints relating to SLR
    constraints = [
        # Thermal expansion
        GlobalConstraint(
            lambda m, t: m.slr_thermal[t]
            == slr_thermal_expansion(m.slr_thermal[t - 1], m.temperature[t - 1], m)
            if t > 0
            else Constraint.Skip,
            name="SLR_thermal",
        ),
        GlobalInitConstraint(
            lambda m: m.slr_thermal[0]
            == m.slr_thermal_init
            + m.slr_thermal_adjust_rate
            * (m.T0 * m.slr_thermal_equil - m.slr_thermal_init)
        ),
        # GSIC
        GlobalConstraint(
            lambda m, t: m.slr_cumgsic[t]
            == slr_gsic(m.slr_cumgsic[t - 1], m.temperature[t - 1], m)
            if t > 0
            else Constraint.Skip,
            name="SLR_GSIC",
        ),
        GlobalInitConstraint(lambda m: m.slr_cumgsic[0] == 0.015),
        # GIS
        GlobalConstraint(
            lambda m, t: m.slr_cumgis[t]
            == slr_gis(m.slr_cumgis[t - 1], m.temperature[t - 1], m)
            if t > 0
            else Constraint.Skip,
            name="SLR_GIS",
        ),
        GlobalInitConstraint(lambda m: m.slr_cumgis[0] == 0.006),
        # Total SLR is sum of each contributing factors
        GlobalConstraint(
            lambda m, t: m.total_SLR[t]
            == m.slr_thermal[t] + m.slr_cumgsic[t] + m.slr_cumgis[t],
            name="total_SLR",
        ),
    ]

    return constraints


def slr_thermal_expansion(slr_thermal, temperature, m: AbstractModel):
    """Calculates next-step SLR due to thermal expansian"""

    equilib = m.slr_thermal_equil
    adjust_rate = m.slr_thermal_adjust_rate

    return (1 - adjust_rate) ** (m.dt / 10) * slr_thermal + adjust_rate * (
        m.dt / 10
    ) * (temperature * equilib)


def slr_gsic(cumgsic, temperature, m: AbstractModel):
    """Calculates next-step SLR due to glaciers and small ice caps"""

    melt_rate = m.slr_gsic_melt_rate
    total_ice = m.slr_gsic_total_ice
    equil_temp = m.slr_gsic_equil_temp

    return cumgsic + melt_rate / total_ice * m.dt * (total_ice - cumgsic) * (
        temperature - equil_temp
    )


def slr_gis(cumgis, temperature, m: AbstractModel):
    """Calculates next-step SLR due to the Greenland ice sheet"""

    melt_rate_above_thresh = m.slr_gis_melt_rate_above_thresh
    init_melt_rate = m.slr_gis_init_melt_rate
    init_ice_vol = m.slr_gis_init_ice_vol

    return cumgis + (m.dt / 10) * (1 / 100) * (
        melt_rate_above_thresh * temperature + init_melt_rate
    ) * (1 - cumgis / init_ice_vol)
