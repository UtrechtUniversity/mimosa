"""
Model equations and constraints:
ecosystem damages for selected services of tropical forest biome from VegClim and ESVD (data extracted 19/06/2025)
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalEquation,
    GlobalInitConstraint,
    Constraint,
    NonNegativeReals,
    quant,
    Any,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    constraints = []
    m.ecosystem_recreation_tropical = Var(m.t)
    m.ecosystem_air_filtration_tropical = Var(m.t)
    m.ecosystem_existence_tropical = Var(m.t)
    m.ecosystem_value_tropical = Var(m.t)  # total value of all services together

    LEVEL = "mean"  # Change this to "median", "mean", "mean+1stdev", or "mean+2stdev" to use different coefficients

    ## Median:
    if LEVEL == "median":
        m.air_filtration_a = Param(initialize=679330373)
        m.air_filtration_b = Param(initialize=-5255964766)
        m.air_filtration_c = Param(initialize=43085565830)

        m.recreation_a = Param(initialize=110504407)
        m.recreation_b = Param(initialize=-854970268)
        m.recreation_c = Param(initialize=7008585374)

        m.existence_a = Param(initialize=5434642985)
        m.existence_b = Param(initialize=-42047718127)
        m.existence_c = Param(initialize=344684526638)

    ## Mean:
    elif LEVEL == "mean":
        m.air_filtration_a = Param(initialize=679330373)
        m.air_filtration_b = Param(initialize=-5255964766)
        m.air_filtration_c = Param(initialize=43085565830)

        m.recreation_a = Param(initialize=5615797751)
        m.recreation_b = Param(initialize=-43449308731)
        m.recreation_c = Param(initialize=356174010859)

        m.existence_a = Param(initialize=171236568058)
        m.existence_b = Param(initialize=-1324853575482)
        m.existence_c = Param(initialize=10860434954183)

    ## Mean+1stdev:
    elif LEVEL == "mean+1stdev":
        m.air_filtration_a = Param(initialize=679330373)
        m.air_filtration_b = Param(initialize=-5255964766)
        m.air_filtration_c = Param(initialize=43085565830)

        m.recreation_a = Param(initialize=29392278520)
        m.recreation_b = Param(initialize=-227407603822)
        m.recreation_c = Param(initialize=1864168221059)

        m.existence_a = Param(initialize=1286107498809)
        m.existence_b = Param(initialize=-9950588055215)
        m.existence_c = Param(initialize=81569587719752)

    ## Mean+2stdev:
    elif LEVEL == "mean+2stdev":
        m.air_filtration_a = Param(initialize=679330373)
        m.air_filtration_b = Param(initialize=-5255964766)
        m.air_filtration_c = Param(initialize=43085565830)

        m.recreation_a = Param(initialize=53168989224)
        m.recreation_b = Param(initialize=-411367094615)
        m.recreation_c = Param(initialize=3372163780884)

        m.existence_a = Param(initialize=2400971485070)
        m.existence_b = Param(initialize=-18576294752175)
        m.existence_c = Param(initialize=152278707780325)

    else:
        raise ValueError(f"Unknown ecosystem cost level: {LEVEL}")

    # /1.33 because ESVD is in 2020$ and MIMOSA in 2005$, /1e12 because its in trillions
    constraints.extend(
        [
            GlobalEquation(
                m.ecosystem_air_filtration_tropical,
                lambda m, t: (
                    m.air_filtration_a * m.temperature[t] ** 2
                    + m.air_filtration_b * m.temperature[t]
                    + m.air_filtration_c
                )
                / 1e12
                / 1.33,
            ),
            GlobalEquation(
                m.ecosystem_recreation_tropical,
                lambda m, t: (
                    m.recreation_a * m.temperature[t] ** 2
                    + m.recreation_b * m.temperature[t]
                    + m.recreation_c
                )
                / 1e12
                / 1.33,
            ),
            GlobalEquation(
                m.ecosystem_existence_tropical,
                lambda m, t: (
                    m.existence_a * m.temperature[t] ** 2
                    + m.existence_b * m.temperature[t]
                    + m.existence_c
                )
                / 1e12
                / 1.33,
            ),
            GlobalEquation(
                m.ecosystem_value_tropical,
                lambda m, t: m.ecosystem_air_filtration_tropical[t]
                + m.ecosystem_recreation_tropical[t]
                + m.ecosystem_existence_tropical[t],
            ),
        ]
    )

    return constraints
