import numpy as np
import warnings
from model.common.config import params
from model.common.units import Quant


def get_TFP(region, data_store):
    time = data_store.data_years
    TFP = []
    dt = time[1] - time[0]

    # Parameters
    alpha = params['economics']['GDP']['alpha']
    dk = params['economics']['GDP']['depreciation of capital']
    sr = params['economics']['GDP']['savings rate']

    # Initialise capital
    K0_data = Quant(params['regions'][region]['initial capital'], 'currency_unit', only_magnitude=False)
    K = K0_data.magnitude
    
    # Get data
    GDP_data = data_store.data_values['GDP'][region]
    population_data = data_store.data_values['population'][region]

    for t, GDP, L in zip(time, GDP_data, population_data):
        TFP.append(GDP / calc_GDP(1, L, K, alpha))
        K = (1-dk)**dt * K + dt * sr * GDP

    return np.array(TFP)



def calc_GDP(TFP, L, K, alpha):
    return TFP * L**(1-alpha) * K**alpha



def MAC(a, factor, gamma, beta):
    return gamma * factor * a**beta

def AC(a, factor, gamma, beta):
    return gamma * factor * a**(beta+1) / (beta+1)



def damage_fct(T, coeff, T0=None):
    """Quadratic damage function

    T: temperature
    T0 [None]: if specified, substracts damage at T0
    """
    dmg = coeff * T**2
    if T0 is not None:
        dmg -= coeff * T0**2
    return dmg