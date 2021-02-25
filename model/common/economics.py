"""
Utils to calculate TFP using the Cobb-Douglas equation
"""

import numpy as np


def get_TFP(region, data_store):
    params = data_store.params
    # quant = data_store.quant
    time = data_store.data_years
    TFP = []
    dt = time[1] - time[0]

    # Parameters
    alpha = params["economics"]["GDP"]["alpha"]
    depr_cap = params["economics"]["GDP"]["depreciation of capital"]
    savings_rate = params["economics"]["GDP"]["savings rate"]

    # Initialise capital
    capital = params["regions"][region][
        "initial capital factor"
    ] * data_store.data_object("GDP")(time[0], region)

    # Get data
    GDP_data = data_store.data_values["GDP"][region]
    population_data = data_store.data_values["population"][region]

    for GDP, pop in zip(GDP_data, population_data):
        TFP.append(GDP / calc_GDP(1, pop, capital, alpha))
        dKdt = calc_dKdt(capital, depr_cap, savings_rate * GDP, dt)
        capital = dKdt * dt + capital

    return np.array(TFP)


def calc_dKdt(K, dk, I, dt):
    return ((1 - dk) ** dt - 1) / dt * K + I


def calc_GDP(TFP, L, K, alpha):
    return TFP * L ** (1 - alpha) * K ** alpha

