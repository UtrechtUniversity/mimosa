"""Shared sets and input parameters used by MIMOSA's model components."""

from mimosa.common import AbstractModel, Param, Set, quant


def create_base_model() -> AbstractModel:
    """Create the abstract model with shared time, region and baseline inputs."""
    m = AbstractModel()

    # Time and region
    m.beginyear = Param()
    m.dt = Param()
    m.tf = Param()
    m.t = Set()
    m.year = None  # Initialised with concrete instance
    m.year2100 = Param()

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
    m.ssp_baseline_emissions = Param(
        m.t,
        m.regions,
        doc="timeandregional::emissions",
        units=quant.unit("emissionsrate_unit"),
    )
    m.MAC_SSP_calibration_factor = Param(m.t, units=quant.unit("dimensionless"))

    return m
