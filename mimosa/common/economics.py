"""
Utils to calculate TFP using the Cobb-Douglas equation
"""

import numpy as np
from mimosa.common.data.utils import UnitValues
from mimosa.common.regional_params import RegionalParamStore


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
    """
    $$ \\frac{\\partial K_{t,r}}{\\partial t} = \\frac{1}{\\Delta t} \\cdot ((1 - dk)^{\\Delta t}  - 1) \\cdot K_{t,r} + I_{t,r}.$$
    """
    return ((1 - dk) ** dt - 1) / dt * K + I


def calc_GDP(TFP, L, K, alpha):
    """
    $$ \\text{GDP}_{\\text{gross},t,r} = \\text{TFP}\\_{t,r} \\cdot L^{1-\\alpha}\\_{t,r} \\cdot K^{\\alpha}\\_{t,r}, $$
    with $\\text{TFP}$ the total factor productivity (exogenously calibrated from the baseline SSP scenarios)
    $L$ the labor (represented by the total population), $K$ the capital stock and $\\alpha$ the share of capital in the production function.

    """
    return TFP * L ** (1 - alpha) * K**alpha
