"""Shared sets and input parameters used by MIMOSA's model components."""

from mimosa.common import AbstractModel, Param, Set, quant


def create_base_model() -> AbstractModel:
    """Create the abstract model with shared time, region and baseline inputs."""
    m = AbstractModel()

    # Time and region
    m.beginyear = Param()
    m.tf = Param()
    m.t = Set()
    m.period_length = Param(m.t)
    m.year = None  # Initialised with concrete instance

    m.regions = Set(ordered=True)

    # Baseline population, GDP and emissions
    m.population = Param(
        m.t,
        m.regions,
        doc="timeandregional::population",
        units=quant.unit("billion people"),
    )
    m.global_population = Param(
        m.t,
        initialize=lambda m, t: sum(m.population[t, r] for r in m.regions),
        units=quant.unit("billion people"),
    )
    m.baseline_GDP = Param(
        m.t,
        m.regions,
        doc="timeandregional::GDP",
        units=quant.unit("currency_unit"),
    )
    m.global_baseline_GDP = Param(
        m.t,
        initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
    )
    # Regional factor to convert 2017 MER dollars to 2010 PPP dollars.
    m.gdp_ppp_2010_div_gdp_mer_2010 = Param(
        m.regions, doc="regional::economics.gdp_ppp_2010_div_gdp_mer_2010"
    )
    m.dollar_2017_MER_to_2010_PPP = Param(
        m.regions,
        initialize=lambda m, r: 0.89632 * m.gdp_ppp_2010_div_gdp_mer_2010[r],
    )
    m.ssp_baseline_emissions = Param(
        m.t,
        m.regions,
        doc="timeandregional::emissions",
        units=quant.unit("emissionsrate_unit"),
    )
    m.MAC_SSP_calibration_factor = Param(m.t, units=quant.unit("dimensionless"))

    return m
