"""
Model equations and constraints:
Effort sharing
"""

import os
import pandas as pd
import numpy as np

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    Constraint,
    RegionalConstraint,
    RegionalEquation,
    GlobalEquation,
    RegionalSoftEqualityConstraint,
    Any,
    quant,
    value,
    soft_min,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "equal_mitigation_costs"
    model = MIMOSA(params)
    ```

    TODO

    """

    historical_emissions, historical_population = _load_data()
    m.effort_sharing_ecpc_discount_rate = Param(
        doc="::effort sharing.ecpc_discount_rate"
    )
    m.effort_sharing_ecpc_start_year = Param(doc="::effort sharing.ecpc_start_year")
    m.effort_sharing_ecpc_debt = Param(
        m.regions,
        initialize=lambda m, r: _calc_debt(
            m, r, historical_emissions, historical_population
        ),
    )

    m.effort_sharing_common_level = Var(m.t, units=quant.unit("fraction_of_GDP"))

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.rel_mitigation_costs[t, r],
            lambda m, t, r: m.effort_sharing_common_level[t],
            "effort_sharing_regime_mitigation_costs",
        ),
    ]


def _load_data():
    """
    Load the CSV files for historical emissions and population (data comes from Our World in Data)
    """
    data_folder = os.path.join(os.path.dirname(__file__), "../../inputdata/data/")
    historical_emissions = pd.read_csv(
        os.path.join(
            data_folder, "historical_emissions/historical_emissions_image_regions.csv"
        )
    ).set_index("Year")
    historical_population = pd.read_csv(
        os.path.join(data_folder, "historical_population/historical_population.csv")
    ).set_index("Year")

    return historical_emissions, historical_population


def _calc_debt(m, r, all_emissions, all_population):
    """
    Calculate the debt for a region based on historical emissions and population.
    The debt is calculated as the cumulative emissions per capita from 1850 to 2020,
    discounted by a given rate.
    """
    start_year = value(m.effort_sharing_ecpc_start_year)
    base_year = value(m.beginyear)

    emissions = all_emissions.loc[start_year:base_year]
    population = all_population.loc[start_year:base_year]
    global_emissions = emissions.sum(axis=1)
    global_population = population.sum(axis=1)

    years = global_population.index
    discount_factor = pd.Series(
        np.exp(-m.effort_sharing_ecpc_discount_rate * (base_year - years)),
        index=years,
    )

    fair_share = population[r] / global_population * global_emissions
    cumulative_discounted_debt = ((fair_share - emissions[r]) * discount_factor).sum()

    return float(cumulative_discounted_debt)
