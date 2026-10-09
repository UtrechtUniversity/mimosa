"""Shared sets and input parameters used by MIMOSA's model components."""

from mimosa.common import ConcreteModel, Param, Set, quant
from mimosa.core.model_inputs import ModelInputs


def create_base_model(inputs: ModelInputs) -> ConcreteModel:
    """Create initialized shared time, region and baseline inputs."""
    m = ConcreteModel()

    # Time and region
    m.beginyear = Param(initialize=inputs.config("time.start"))
    m.tf = Param(initialize=len(inputs.t) - 1)
    m.t = Set(initialize=inputs.t)
    m.period_length = Param(
        m.t, initialize=dict(enumerate(inputs.time_grid.period_lengths))
    )
    m.year = inputs.year

    m.regions = Set(initialize=inputs.regions, ordered=True)

    # Baseline population, GDP and emissions
    m.population = Param(
        m.t,
        m.regions,
        initialize=inputs.time_regional("population"),
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
        initialize=inputs.time_regional("GDP"),
        units=quant.unit("currency_unit"),
    )
    m.global_baseline_GDP = Param(
        m.t,
        initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
    )
    # Regional factor to convert 2017 MER dollars to 2010 PPP dollars.
    m.gdp_ppp_2010_div_gdp_mer_2010 = Param(
        m.regions,
        initialize=inputs.regional("economics", "gdp_ppp_2010_div_gdp_mer_2010"),
    )
    m.dollar_2017_MER_to_2010_PPP = Param(
        m.regions,
        initialize=lambda m, r: 0.89632 * m.gdp_ppp_2010_div_gdp_mer_2010[r],
    )
    m.ssp_baseline_emissions = Param(
        m.t,
        m.regions,
        initialize=inputs.time_regional("emissions"),
        units=quant.unit("emissionsrate_unit"),
    )
    return m
