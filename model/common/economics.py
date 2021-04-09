"""
Utils to calculate TFP using the Cobb-Douglas equation
"""

import numpy as np
from model.common.data.utils import UnitValues
from model.common.regional_params import RegionalParamStore


def get_TFP(
    region,
    years,
    gdp_all_regions,
    population_all_regions,
    regional_param_store: RegionalParamStore,
) -> UnitValues:
    params = regional_param_store.params
    # quant = data_store.quant
    tfp = []
    dt = years[1] - years[0]

    # Parameters
    alpha = params["economics"]["GDP"]["alpha"]
    depr_cap = params["economics"]["GDP"]["depreciation of capital"]
    savings_rate = params["economics"]["GDP"]["savings rate"]

    # Get data
    gdp_data = gdp_all_regions[region]
    population_data = population_all_regions[region]

    # Initialise capital
    capital = (
        regional_param_store.getregional("economics", "init_capital_factor", region)
        * gdp_data.yvalues[0]
    )

    for gdp, pop in zip(gdp_data.yvalues, population_data.yvalues):
        tfp.append(gdp / calc_GDP(1, pop, capital, alpha))
        dKdt = calc_dKdt(capital, depr_cap, savings_rate * gdp, dt)
        capital = dKdt * dt + capital

    return UnitValues(gdp_data.xvalues, np.array(tfp))


def calc_dKdt(K, dk, I, dt):
    return ((1 - dk) ** dt - 1) / dt * K + I


def calc_GDP(TFP, L, K, alpha):
    return TFP * L ** (1 - alpha) * K ** alpha

