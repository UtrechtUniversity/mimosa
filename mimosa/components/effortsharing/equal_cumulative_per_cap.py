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
    RegionalInitConstraint,
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
    params["effort sharing"]["regime"] = "equal_cumulative_per_capita"
    model = MIMOSA(params)
    ```

    The equal cumulative per capita (ECPC) regime allocates emission allowances based on **historical and future** cumulative
    emissions per capita. Contrary to the other effort sharing regimes, this regime considers only the cumulative emissions,
    not the distribution over time: the only constraint will be on the cumulative emissions at the end of the time horizon.
    MIMOSA is then free to allocate these reductions over time.

    First, a historical debt is calculated for each region: how much more, or less, emissions did a region emit
    compared to its fair share of cumulative emissions per capita since a start year (by default 1850).


    :::mimosa.components.effortsharing.equal_cumulative_per_cap._calc_debt

    #### Step 2: Regional cumulative emissions

    Once the historical debt is calculated, the future cumulative regional allowances are calculated as:

    $$
    \\text{cumulative allowances}_{r} = \\frac{\\sum_{t=2020}^{2100} \\text{population}_{t,r}}{\\sum_{t=2020}^{2100} \\text{global population}_{t}} \\cdot \\text{cumulative emissions}_{2100} + \\text{debt}_{r},
    $$

    where $\\text{cumulative emissions}_{2100}$ is the total global emissions at the end of the time horizon.

    *Note: if the time horizon is different than 2100, replace 2100 with the actual time horizon.*


    """

    historical_emissions, historical_population = _load_data()
    m.effort_sharing_ecpc_discount_rate = Param(
        doc="::effort sharing.ecpc_discount_rate"
    )
    m.effort_sharing_ecpc_start_year = Param(doc="::effort sharing.ecpc_start_year")
    m.effort_sharing_ecpc_historical_debt = Param(
        m.t,  # Constant over time
        m.regions,
        initialize=lambda m, t, r: _calc_debt(
            m, r, historical_emissions, historical_population
        ),
        units=quant.unit("emissions_unit"),
    )

    m.cumulative_regional_emission_allowances = Var(
        m.t, m.regions, units=quant.unit("emissions_unit")
    )

    m.effort_sharing_ecpc_cumulative_allowances = Var(
        m.t, m.regions, units=quant.unit("emissions_unit")
    )
    m.cumulative_population_share = Param(
        m.t,
        m.regions,
        initialize=lambda m, t, r: sum(m.population[s, r] for s in range(t + 1))
        / sum(m.global_population[s] for s in range(t + 1)),
    )

    return [
        # ECPC needs regional carbon budget, so calculate regional cumulative emissions
        RegionalEquation(
            m.cumulative_regional_emission_allowances,
            lambda m, t, r: (
                m.cumulative_regional_emission_allowances[t - 1, r] if t > 0 else 0
            )
            + m.dt * (m.baseline[t, r] - m.paid_for_emission_reductions[t, r]),
        ),
        # # Then impose the effort sharing constraint
        RegionalEquation(
            m.effort_sharing_ecpc_cumulative_allowances,
            lambda m, t, r: m.cumulative_population_share[t, r]
            * m.cumulative_emissions[t]
            + m.effort_sharing_ecpc_historical_debt[t, r],
        ),
        RegionalSoftEqualityConstraint(
            # Note: add constant factor to LHS and RHS to make sure both sides are positive
            lambda m, t, r: m.cumulative_regional_emission_allowances[t, r] + 500,
            lambda m, t, r: m.effort_sharing_ecpc_cumulative_allowances[t, r] + 500,
            "effort_sharing_ecpc",
            ignore_if=lambda m, t, r: t != m.year2100,
        ),
        # Stability constraint to ensure that the relative mitigation costs do not exceed a certain threshold
        RegionalConstraint(lambda m, t, r: m.rel_mitigation_costs[t, r] <= 0.5),
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

    #### Step 1: historical debt calculation

    Calculate the debt for a region based on historical emissions and population.
    The debt is calculated as the cumulative emissions per capita from a start year to 2020,
    discounted by a given rate:

    $$
    \\text{debt}_{r} = \\sum_{t=\\text{start year}}^{2020} \\left(\\frac{\\text{population}_{r,t}}{\\text{global population}_{t}} \\cdot \\text{global emissions}_{t} - \\text{emissions}_{r,t}\\right) \\cdot e^{-\\text{discount rate} \\cdot (2020 - t)}.
    $$

    where you can set the following parameters:

    * $\\text{start year}$ using [`params["effort sharing"]["ecpc_start_year"]`](../parameters.md#effort sharing.ecpc_start_year) (default: 1850),
    * $\\text{discount rate}$ using [`params["effort sharing"]["ecpc_start_year"]`](../parameters.md#effort sharing.ecpc_discount_rate) (default: 3%/yr).

    The historical debt is therefore positive for regions that emitted more than their fair share of cumulative emissions per capita, and negative for regions that emitted less than their fair share:

    ``` plotly
    {"file_path": "./assets/plots/ecpc_debt.json"}
    ```
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
