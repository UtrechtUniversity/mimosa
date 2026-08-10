"""
Global mean sea-level rise (height, not sea-level-rise damages).

The component is a deterministic reduced-complexity model inspired by the
response equations in BRICK, SURFER, SIMPLE, and LARMIP-2. Its central parameter
set is intended to reproduce the order of magnitude and component balance of
IPCC AR6 median projections. All contributions use 1900 as their common
reference year.
"""

from typing import Sequence

from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalEquation,
    NonNegativeReals,
    exp,
    tanh,
    quant,
    ModelContext,
)


# Coherent deterministic response sets. Historical initial conditions and ice
# potentials are deliberately shared: these sets describe uncertainty in future
# physical response, rather than uncertainty in observed present-day sea level.
SLR_PROJECTION_PARAMETER_SETS = {
    "low": {
        "thermal_fast_sensitivity": 0.075,
        "thermal_slow_sensitivity": 0.255,
        "thermal_fast_timescale": 42.5,
        "thermal_slow_timescale": 425.0,
        "gsic_temp_sensitivity": 2.4,
        "gsic_timescale": 120.0,
        "gis_threshold": 2.0,
        "gis_transition_width": 0.7,
        "gis_base_timescale": 6500.0,
        "gis_timescale_sensitivity": 0.2,
        "ais_ocean_temp_scaling": 0.45,
        "ais_ocean_temp_timescale": 50.0,
        "ais_background_rate": 0.0009,
        "ais_temp_sensitivity": 0.0002,
        "ais_fast_rate": 0.0,
        "ais_fast_threshold": 3.0,
        "ais_fast_transition_width": 0.2,
    },
    "central": {
        "thermal_fast_sensitivity": 0.080,
        "thermal_slow_sensitivity": 0.270,
        "thermal_fast_timescale": 40.0,
        "thermal_slow_timescale": 400.0,
        "gsic_temp_sensitivity": 2.0,
        "gsic_timescale": 110.0,
        "gis_threshold": 1.8,
        "gis_transition_width": 0.6,
        "gis_base_timescale": 6000.0,
        "gis_timescale_sensitivity": 0.3,
        "ais_ocean_temp_scaling": 0.60,
        "ais_ocean_temp_timescale": 30.0,
        "ais_background_rate": 0.0011,
        "ais_temp_sensitivity": 0.00025,
        "ais_fast_rate": 0.005,
        "ais_fast_threshold": 2.5,
        "ais_fast_transition_width": 0.15,
    },
    "high": {
        "thermal_fast_sensitivity": 0.100,
        "thermal_slow_sensitivity": 0.340,
        "thermal_fast_timescale": 30.0,
        "thermal_slow_timescale": 300.0,
        "gsic_temp_sensitivity": 1.6,
        "gsic_timescale": 140.0,
        "gis_threshold": 1.4,
        "gis_transition_width": 0.5,
        "gis_base_timescale": 4000.0,
        "gis_timescale_sensitivity": 0.4,
        "ais_ocean_temp_scaling": 0.80,
        "ais_ocean_temp_timescale": 20.0,
        "ais_background_rate": 0.0012,
        "ais_temp_sensitivity": 0.00035,
        "ais_fast_rate": 0.012,
        "ais_fast_threshold": 1.8,
        "ais_fast_transition_width": 0.12,
    },
}


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    r"""
    The sea-level-rise (SLR) component represents thermal expansion, glaciers,
    the Greenland ice sheet (GIS), the Antarctic ice sheet (AIS), and future
    changes in land-water storage (LWS). The formulation is deliberately small
    and deterministic so it can be evaluated both by the MIMOSA simulator and
    as part of the Pyomo optimisation model.

    All component values are expressed as metres above the 1900 global mean
    sea-level reference. The values at the model start are linearly interpolated
    between zero in 1900 and the central 2025 estimates below. This makes the
    reference year explicit and prevents a run starting before 2025 from using
    2025 sea-level values.

    The component option `projection` selects a coherent `low`, `central`, or
    `high` deterministic response set. The sets use identical historical
    initial conditions, but different sensitivities, response times, and AIS
    fast-response assumptions. The default is `central`.

    The projection can be selected before model construction with:

    ```python
    params["model structure"]["sealevelrise options"]["projection"] = "high"
    ```

    # Thermal expansion

    Thermal expansion is represented by a fast and a slow response box. Each
    box relaxes towards a temperature-dependent equilibrium:

    $$
    S_{i,t}=\beta_i T_{t-1}+
    \left(S_{i,t-1}-\beta_i T_{t-1}\right)e^{-\Delta t/\tau_i},
    \qquad i\in\{\text{fast},\text{slow}\}.
    $$

    The exact exponential update makes the response independent of the chosen
    numerical time step for a constant temperature forcing.

    This two-timescale equation is a reduced-form approximation chosen for
    MIMOSA, rather than a direct reproduction of an ocean model. The first-order
    relaxation form follows BRICK v0.2 (Wong et al., 2017, Sect. 3.2.4,
    Eqs. 9--10). Splitting it into fast and slow boxes represents the upper- and
    deep-ocean distinction in SURFER v2.0 (Martínez Montero et al., 2022,
    Sects. 2.3.1 and 2.4.3). MIMOSA's equilibrium sensitivities and response
    times are calibrated jointly against the AR6 thermal-expansion contributions
    in Table 9.9 of Fox-Kemper et al. (2021); they are not the coefficients from
    either BRICK or SURFER.

    # Glaciers

    The glacier contribution relaxes towards the capped equilibrium proposed
    by Martínez Montero et al. (2022):

    $$
    S^*_{\mathrm{GL}}(T)=P_{\mathrm{GL}}
    \tanh\left(\frac{T}{\zeta_{\mathrm{GL}}}\right),
    $$

    $$
    S_{\mathrm{GL},t}=S^*_{\mathrm{GL}}(T_{t-1})+
    \left(S_{\mathrm{GL},t-1}-S^*_{\mathrm{GL}}(T_{t-1})\right)
    e^{-\Delta t/\tau_{\mathrm{GL}}}.
    $$

    This replaces the previous formulation, in which all glaciers eventually
    melted under any sustained temperature above -1 degree C.

    # Greenland ice sheet

    Greenland follows a SIMPLE-style delayed equilibrium. Its equilibrium
    contribution is a normalised logistic function bounded by the ice sheet's
    sea-level potential. Its response time decreases smoothly with warming:

    $$
    S^*_{\mathrm{GIS}}(T)=P_{\mathrm{GIS}}
    \frac{\sigma((T-T_c)/w)-\sigma(-T_c/w)}
         {1-\sigma(-T_c/w)},
    $$

    $$
    \tau_{\mathrm{GIS}}(T)=\tau_0e^{-\gamma T}.
    $$

    # Antarctic ice sheet

    A single lagged Antarctic subsurface-ocean temperature proxy drives the AIS
    response. A smooth threshold term represents the possibility of faster ice
    loss at high warming while retaining differentiability for optimisation:

    $$
    T_{A,t}=\lambda_A T_{t-1}+
    \left(T_{A,t-1}-\lambda_A T_{t-1}\right)e^{-\Delta t/\tau_A},
    $$

    $$
    S_{\mathrm{AIS},t}=S_{\mathrm{AIS},t-1}+\Delta t
    \left[r_0+r_1T_{A,t}+r_f\sigma((T_{A,t}-T_{crit})/w_A)\right]
    \left(1-\frac{S_{\mathrm{AIS},t-1}}{P_{\mathrm{AIS}}}\right).
    $$

    The scaling and delay between global surface warming and Antarctic
    subsurface-ocean warming are motivated by LARMIP-2 (Levermann et al., 2020,
    Sect. 2.2). The AIS rate equation itself is a deliberately simpler MIMOSA
    parameterisation, not a reproduction of LARMIP-2 or SURFER. Its smooth fast
    term is inspired by the threshold representation of uncertain rapid
    Antarctic disintegration in Wong et al. (2017). The ordinary background and
    temperature-response rates are calibrated against the AR6 AIS contributions
    in Table 9.9. The high parameter set is intended as a low-likelihood,
    high-impact sensitivity case and not as the upper endpoint of the AR6 likely
    range.

    # Land-water storage

    AR6 projects an approximately scenario-independent land-water contribution
    of 0.03 m between 1995--2014 and 2100. Because the historical contribution
    is already implicit in MIMOSA's 2025 initial total, only its future anomaly
    is added explicitly:

    $$
    S_{\mathrm{LWS},t}=S_{\mathrm{LWS},t-1}+\Delta t\,r_{\mathrm{LWS}},
    \qquad r_{\mathrm{LWS}}=0.0004\ \mathrm{m\,yr^{-1}}.
    $$

    # Total sea-level rise

    $$
    S_t=S_{\mathrm{thermal},t}+S_{\mathrm{GL},t}
        +S_{\mathrm{GIS},t}+S_{\mathrm{AIS},t}+S_{\mathrm{LWS},t}.
    $$

    ## Calibration against IPCC AR6

    The process papers motivate the compact equation forms; they do not imply
    that every coefficient is transferred unchanged. The three coherent
    parameter sets are outcome-calibrated against AR6 WGI Table 9.9 and the
    warming-level assessment in Chapter 12. Consequently, increasing the
    glacier or ordinary AIS response remains consistent with the cited equation
    structure while bringing total SLR into the assessed AR6 ranges. The
    following benchmark prescribes a linear warming path from 1.27 degrees C in
    2025 to the stated 2100 warming level. Values are metres relative to 1900:

    | 2100 warming | AR6 median [likely range] | low | central | high |
    | ------------ | ------------------------- | --- | ------- | ---- |
    | 2 degrees C  | 0.668 [0.558--0.848]      | 0.550 | 0.624 | 0.831 |
    | 3 degrees C  | 0.778 [0.658--0.968]      | 0.652 | 0.751 | 1.176 |
    | 4 degrees C  | 0.858 [0.738--1.068]      | 0.749 | 0.873 | 1.549 |

    AR6 Chapter 12 reports the warming-level values relative to 1995--2014.
    The table adds the assessed 0.158 m rise from 1900 to 1995--2014, following
    the AR6 Summary for Policymakers. The comparison is a calibration diagnostic,
    not a claim that a warming level uniquely determines SLR: the preceding
    temperature pathway and rate of warming also affect the lagged components.

    Under this diagnostic, the low set tracks the lower edge of the AR6 likely
    range and central remains within it. High exceeds the likely range at 3 and
    4 degrees C by design, representing rapid Antarctic loss. For transparency,
    the central 2100 component values at 2, 3, and 4 degrees C respectively are:

    | Component | 2 degrees C | 3 degrees C | 4 degrees C |
    | --------- | -----------: | -----------: | -----------: |
    | Thermal expansion | 0.219 | 0.283 | 0.347 |
    | Glaciers | 0.152 | 0.169 | 0.178 |
    | Greenland | 0.103 | 0.147 | 0.193 |
    | Antarctica | 0.120 | 0.122 | 0.125 |
    | Land-water storage | 0.030 | 0.030 | 0.030 |

    References:

    - [Fox-Kemper et al. (2021), IPCC AR6 WGI Chapter 9](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-9/).
    - [IPCC AR6 WGI Chapter 12, climate impact-driver projections](https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-12/).
    - [IPCC AR6 WGI Summary for Policymakers](https://www.ipcc.ch/report/ar6/wg1/chapter/summary-for-policymakers/).
    - [Bakker, Applegate and Keller (2016), SIMPLE](https://doi.org/10.1016/j.envsoft.2016.05.003).
    - [Martínez Montero et al. (2022), SURFER v2.0](https://doi.org/10.5194/gmd-15-8059-2022).
    - [Wong et al. (2017), BRICK v0.2](https://doi.org/10.5194/gmd-10-2741-2017).
    - [Levermann et al. (2020), LARMIP-2](https://doi.org/10.5194/esd-11-35-2020).
    - [Wong, Bakker and Keller (2017), Antarctic fast dynamics](https://doi.org/10.1007/s10584-017-2039-4).
    """

    projection = context.option("sealevelrise", "projection", default="central")
    try:
        slr_params = SLR_PROJECTION_PARAMETER_SETS[projection]
    except KeyError as exc:
        valid = ", ".join(SLR_PROJECTION_PARAMETER_SETS)
        raise ValueError(
            f"Unknown SLR projection parameter set '{projection}'. "
            f"Expected one of: {valid}."
        ) from exc

    # A common reference year and rounded central component values at the
    # default model start. Their 0.23 m sum is consistent with the assessed
    # historical rise and recent component trends. Values are metres of global
    # mean SLR above the 1900 reference.
    m.slr_reference_year = Param(initialize=1900)
    m.slr_initial_year = Param(initialize=2025)

    # Thermal expansion: fast upper-ocean and slow deep-ocean response boxes.
    m.slr_thermal_fast = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_thermal_slow = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_thermal = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_thermal_fast_init = Param(initialize=0.045)
    m.slr_thermal_slow_init = Param(initialize=0.025)
    m.slr_thermal_fast_sensitivity = Param(
        initialize=slr_params["thermal_fast_sensitivity"]
    )
    m.slr_thermal_slow_sensitivity = Param(
        initialize=slr_params["thermal_slow_sensitivity"]
    )
    m.slr_thermal_fast_timescale = Param(
        initialize=slr_params["thermal_fast_timescale"]
    )
    m.slr_thermal_slow_timescale = Param(
        initialize=slr_params["thermal_slow_timescale"]
    )

    # Glaciers. The 0.32 m potential follows the AR6 parametric extrapolation.
    m.slr_cumgsic = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_gsic_init = Param(initialize=0.090)
    m.slr_gsic_total_ice = Param(initialize=0.32)
    m.slr_gsic_temp_sensitivity = Param(
        initialize=slr_params["gsic_temp_sensitivity"]
    )
    m.slr_gsic_timescale = Param(initialize=slr_params["gsic_timescale"])

    # Greenland. The potential is the sea-level equivalent of the full ice
    # sheet; the remaining parameters govern equilibrium and response speed.
    m.slr_cumgis = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_gis_init = Param(initialize=0.045)
    m.slr_gis_total_ice = Param(initialize=7.3)
    m.slr_gis_threshold = Param(initialize=slr_params["gis_threshold"])
    m.slr_gis_transition_width = Param(
        initialize=slr_params["gis_transition_width"]
    )
    m.slr_gis_base_timescale = Param(
        initialize=slr_params["gis_base_timescale"]
    )
    m.slr_gis_timescale_sensitivity = Param(
        initialize=slr_params["gis_timescale_sensitivity"]
    )

    # Antarctica. The proxy temperature is in degrees C above pre-industrial;
    # rates are metres of sea-level equivalent per year.
    m.slr_antarctic_ocean_temp = Var(
        m.t, units=quant.unit("degC_above_PI")
    )
    m.slr_ais_ocean_temp_init = Param(initialize=0.30)
    m.slr_ais_ocean_temp_scaling = Param(
        initialize=slr_params["ais_ocean_temp_scaling"]
    )
    m.slr_ais_ocean_temp_timescale = Param(
        initialize=slr_params["ais_ocean_temp_timescale"]
    )
    m.slr_cumais = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_ais_init = Param(initialize=0.025)
    # Effective vulnerable Antarctic stock, rather than the full AIS potential.
    m.slr_ais_total_ice = Param(initialize=5.0)
    m.slr_ais_background_rate = Param(
        initialize=slr_params["ais_background_rate"]
    )
    m.slr_ais_temp_sensitivity = Param(
        initialize=slr_params["ais_temp_sensitivity"]
    )
    m.slr_ais_fast_rate = Param(initialize=slr_params["ais_fast_rate"])
    m.slr_ais_fast_threshold = Param(
        initialize=slr_params["ais_fast_threshold"]
    )
    m.slr_ais_fast_transition_width = Param(
        initialize=slr_params["ais_fast_transition_width"]
    )

    # Future land-water-storage anomaly. Its historical contribution is
    # implicit in the common 2025 initial total, avoiding double counting.
    m.slr_cumlws = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))
    m.slr_lws_rate = Param(initialize=0.0004)

    m.total_SLR = Var(m.t, within=NonNegativeReals, units=quant.unit("m"))

    constraints = [
        GlobalEquation(
            m.slr_thermal_fast,
            lambda m, t: (
                slr_thermal_expansion(
                    m.slr_thermal_fast[t - 1],
                    m.temperature[t - 1],
                    m.slr_thermal_fast_sensitivity,
                    m.slr_thermal_fast_timescale,
                    m,
                )
                if t > 0
                else slr_initial_value(m.slr_thermal_fast_init, m)
            ),
        ),
        GlobalEquation(
            m.slr_thermal_slow,
            lambda m, t: (
                slr_thermal_expansion(
                    m.slr_thermal_slow[t - 1],
                    m.temperature[t - 1],
                    m.slr_thermal_slow_sensitivity,
                    m.slr_thermal_slow_timescale,
                    m,
                )
                if t > 0
                else slr_initial_value(m.slr_thermal_slow_init, m)
            ),
        ),
        GlobalEquation(
            m.slr_thermal,
            lambda m, t: m.slr_thermal_fast[t] + m.slr_thermal_slow[t],
        ),
        GlobalEquation(
            m.slr_cumgsic,
            lambda m, t: (
                slr_gsic(m.slr_cumgsic[t - 1], m.temperature[t - 1], m)
                if t > 0
                else slr_initial_value(m.slr_gsic_init, m)
            ),
        ),
        GlobalEquation(
            m.slr_cumgis,
            lambda m, t: (
                slr_gis(m.slr_cumgis[t - 1], m.temperature[t - 1], m)
                if t > 0
                else slr_initial_value(m.slr_gis_init, m)
            ),
        ),
        GlobalEquation(
            m.slr_antarctic_ocean_temp,
            lambda m, t: (
                slr_antarctic_ocean_temperature(
                    m.slr_antarctic_ocean_temp[t - 1],
                    m.temperature[t - 1],
                    m,
                )
                if t > 0
                else slr_initial_value(m.slr_ais_ocean_temp_init, m)
            ),
        ),
        GlobalEquation(
            m.slr_cumais,
            lambda m, t: (
                slr_ais(
                    m.slr_cumais[t - 1],
                    m.slr_antarctic_ocean_temp[t],
                    m,
                )
                if t > 0
                else slr_initial_value(m.slr_ais_init, m)
            ),
        ),
        GlobalEquation(
            m.slr_cumlws,
            lambda m, t: (
                m.slr_cumlws[t - 1] + m.dt * m.slr_lws_rate
                if t > 0
                else 0.0
            ),
        ),
        GlobalEquation(
            m.total_SLR,
            lambda m, t: (
                m.slr_thermal[t]
                + m.slr_cumgsic[t]
                + m.slr_cumgis[t]
                + m.slr_cumais[t]
                + m.slr_cumlws[t]
            ),
        ),
    ]

    return constraints


def slr_initial_value(value_at_initial_year, m: AbstractModel):
    """Interpolate a component value from the common reference year.

    The central initial values are specified for 2025. Linear interpolation is
    used only for model initialisation; projected changes after the model start
    are governed by the component response equations.
    """

    elapsed = m.beginyear - m.slr_reference_year
    calibration_period = m.slr_initial_year - m.slr_reference_year
    return value_at_initial_year * elapsed / calibration_period


def relax_to_equilibrium(current, equilibrium, timescale, m: AbstractModel):
    """Exact update of a first-order response for one MIMOSA time step."""

    persistence = exp(-m.dt / timescale)
    return equilibrium + (current - equilibrium) * persistence


def slr_thermal_expansion(
    slr_thermal, temperature, sensitivity, timescale, m: AbstractModel
):
    """Update one thermal-expansion response box."""

    equilibrium = sensitivity * temperature
    return relax_to_equilibrium(slr_thermal, equilibrium, timescale, m)


def slr_gsic_equilibrium(temperature, m: AbstractModel):
    """Temperature-dependent equilibrium glacier contribution."""

    return m.slr_gsic_total_ice * tanh(
        temperature / m.slr_gsic_temp_sensitivity
    )


def slr_gsic(cumgsic, temperature, m: AbstractModel):
    """Relax the glacier contribution towards its finite equilibrium."""

    equilibrium = slr_gsic_equilibrium(temperature, m)
    return relax_to_equilibrium(cumgsic, equilibrium, m.slr_gsic_timescale, m)


def logistic(x):
    """Numerically safe logistic for the moderate exponents used here."""

    return 1 / (1 + exp(-x))


def slr_gis_equilibrium(temperature, m: AbstractModel):
    """Bounded Greenland equilibrium contribution, normalised at 0 degree C."""

    threshold = m.slr_gis_threshold
    width = m.slr_gis_transition_width
    preindustrial = logistic(-threshold / width)
    warmed = logistic((temperature - threshold) / width)
    fraction_melted = (warmed - preindustrial) / (1 - preindustrial)
    return m.slr_gis_total_ice * fraction_melted


def slr_gis_timescale(temperature, m: AbstractModel):
    """Greenland response time, decreasing smoothly as warming increases."""

    return m.slr_gis_base_timescale * exp(
        -m.slr_gis_timescale_sensitivity * temperature
    )


def slr_gis(cumgis, temperature, m: AbstractModel):
    """Update the Greenland contribution using delayed equilibrium response."""

    equilibrium = slr_gis_equilibrium(temperature, m)
    timescale = slr_gis_timescale(temperature, m)
    return relax_to_equilibrium(cumgis, equilibrium, timescale, m)


def slr_antarctic_ocean_temperature(ocean_temperature, temperature, m):
    """Update the lagged Antarctic subsurface-ocean temperature proxy."""

    equilibrium = m.slr_ais_ocean_temp_scaling * temperature
    return relax_to_equilibrium(
        ocean_temperature,
        equilibrium,
        m.slr_ais_ocean_temp_timescale,
        m,
    )


def slr_ais_rate(ocean_temperature, m: AbstractModel):
    """Antarctic contribution rate in metres of sea level per year."""

    fast_fraction = logistic(
        (ocean_temperature - m.slr_ais_fast_threshold)
        / m.slr_ais_fast_transition_width
    )
    return (
        m.slr_ais_background_rate
        + m.slr_ais_temp_sensitivity * ocean_temperature
        + m.slr_ais_fast_rate * fast_fraction
    )


def slr_ais(cumais, ocean_temperature, m: AbstractModel):
    """Update the Antarctic contribution, subject to its finite ice stock."""

    remaining_fraction = 1 - cumais / m.slr_ais_total_ice
    return cumais + m.dt * slr_ais_rate(ocean_temperature, m) * remaining_fraction
