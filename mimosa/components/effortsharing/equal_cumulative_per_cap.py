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
    params["effort sharing"]["regime"] = "equal_cumulative_per_cap"
    model = MIMOSA(params)
    ```

    In the equal cumulative per capita (ECPC) regime, emission allowances are allocated based on an equal
    per capita distribution of emissions, combining both *historical* and *future* emissions per capita.
    The historical emission debt is then spread out over the future time steps, going linearly down to
    zero in the repayment end year (default: 2050).

    First, a historical debt is calculated for each region: how much more, or less, emissions did a region emit
    compared to its fair share of cumulative emissions per capita since a start year (by default 1850).


    :::mimosa.components.effortsharing.equal_cumulative_per_cap._calc_debt

    #### Step 2: future fair share (excluding historical debt repayment)

    The future fair share for every region (excluding the historical debt) is equal to the immediate
    per capita convergence regime: every year, a region gets allocated a share of the global emissions
    based on their population share.

    ``` plotly
    {"file_path": "./assets/plots/ecpc_allowances.json"}
    ```


    """

    historical_emissions, historical_population = _load_data()
    m.effortsharing_ecpc_discount_rate = Param(
        doc="::effort sharing.ecpc_discount_rate"
    )
    m.effortsharing_ecpc_start_year = Param(doc="::effort sharing.ecpc_start_year")
    m.effortsharing_ecpc_historical_debt = Param(
        m.t,  # Constant over time
        m.regions,
        initialize=lambda m, t, r: _calc_debt(
            m, r, historical_emissions, historical_population
        ),
        units=quant.unit("emissions_unit"),
    )

    m.percapconv_share_pop = Param(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.population[t, r] / m.global_population[t],
    )

    m.effortsharing_ecpc_repayment_endyear = Param(
        doc="::effort sharing.ecpc_repayment_endyear"
    )

    m.effortsharing_ecpc_annual_debt_repayment = Param(
        m.t,
        m.regions,
        initialize=_calc_ecpc_annual_debt_repayment,
        units=quant.unit("emissionsrate_unit"),
    )

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.percapconv_share_pop[t, r] * m.global_emissions[t]
            - m.effortsharing_ecpc_annual_debt_repayment[t, r],
            lambda m, t, r: m.regional_emission_allowances[t, r],
            epsilon=None,
            absolute_epsilon=0.001,
            ignore_if=lambda m, t, r: t == 0,
            name="percapconv_rule",
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

    #### Step 1: historical debt calculation

    The historical debt is calculated as the cumulative difference between the historical
    fair share (based on equal per capita emissions) and the actual emissions, starting from
    a given start year (default: 1850) until the base year (default: 2020), and then
    discounted by a given rate:

    $$
    \\text{debt}_{r} = \\sum_{t=\\text{start year}}^{2020} \\left(\\text{emissions}_{r,t} - \\frac{\\text{population}_{r,t}}{\\text{emissions}_{r,t}\\text{global population}_{t}} \\cdot \\text{global emissions}_{t}\\right) \\cdot e^{-\\text{discount rate} \\cdot (2020 - t)}.
    $$

    where you can set the following parameters:

    * $\\text{start year}$ using [`params["effort sharing"]["ecpc_start_year"]`](../parameters.md#effort sharing.ecpc_start_year) (default: 1850),
    * $\\text{discount rate}$ using [`params["effort sharing"]["ecpc_start_year"]`](../parameters.md#effort sharing.ecpc_discount_rate) (default: 3%/yr).

    The historical debt is therefore positive for regions that emitted more than their fair share of cumulative emissions per capita, and negative for regions that emitted less than their fair share:

    ``` plotly
    {"file_path": "./assets/plots/ecpc_debt.json"}
    ```
    """
    start_year = value(m.effortsharing_ecpc_start_year)
    base_year = value(m.beginyear)

    emissions = all_emissions.loc[start_year:base_year]
    population = all_population.loc[start_year:base_year]
    global_emissions = emissions.sum(axis=1)
    global_population = population.sum(axis=1)

    years = global_population.index
    discount_factor = pd.Series(
        np.exp(-m.effortsharing_ecpc_discount_rate * (base_year - years)),
        index=years,
    )

    fair_share = population[r] / global_population * global_emissions
    cumulative_discounted_debt = ((emissions[r] - fair_share) * discount_factor).sum()

    return float(cumulative_discounted_debt)


def _calc_ecpc_annual_debt_repayment(m, t, r, corrected=True):
    """
    Compute the ECPC annual debt repayment.

    If `corrected` is True, a normalization factor is applied so that the
    discrete sum of repayments over all time steps equals the historical debt.

    Returns:
        Annual repayment amount for region r in year t
    """

    conv_year = value(m.effortsharing_ecpc_repayment_endyear)

    def _uncorrected(t_idx):
        if conv_year is False or conv_year == 0:
            return m.effortsharing_ecpc_historical_debt[0, r] / (m.tf * m.dt)
        if m.year(t_idx) >= conv_year or t_idx == 0:
            return 0.0
        s = t_idx - 1
        delta_years = conv_year - m.year(1)
        start_level = 2 * m.effortsharing_ecpc_historical_debt[0, r] / delta_years
        return start_level - start_level / delta_years * (m.year(s + 1) - m.year(0))

    uncorrected_value = _uncorrected(t)

    if not corrected:
        return uncorrected_value

    sum_repayments = sum(_uncorrected(s) * m.dt for s in m.t)
    return (
        uncorrected_value / sum_repayments * m.effortsharing_ecpc_historical_debt[0, r]
    )
