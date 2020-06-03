import numpy as np
import warnings
from model.common.config import params
from model.common.units import Quant
from model.common import data


def calc_GDP(TFP, L, K, alpha):
    return TFP * L**(1-alpha) * K**alpha


def get_TFP(time, region):
    TFP = []
    dt = time[1] - time[0]

    # Parameters
    alpha = params['economics']['GDP']['alpha']
    dk = params['economics']['GDP']['depreciation of capital']
    sr = params['economics']['GDP']['savings rate']

    # Initialise capital
    K0_data = Quant(params['regions'][region]['initial capital'], 'currency_unit', only_magnitude=False)
    K = K0_data.magnitude

    GDP_data = data.get_data(time, region, params['SSP'], 'GDP', 'currency_unit')

    # Check units:
    if K0_data.units != GDP_data['unit']:
        warnings.warn("Capital stock unit {} not equal to GDP unit {}.".format(
            K0_data.units, GDP_data['unit']
        ))

    population_data = data.get_data(time, region, params['SSP'], 'population', 'population_unit')

    for t, GDP, L in zip(time, GDP_data['values'], population_data['values']):
        TFP.append(GDP / calc_GDP(1, L, K, alpha))
        K = (1-dk)**dt * K + dt * sr * GDP

    return np.array(TFP)



def MAC(a, factor):
    gamma = Quant(params['economics']['MAC']['gamma'], 'currency_unit/emissionsrate_unit')
    beta = params['economics']['MAC']['beta']
    return gamma * factor * a**beta

def AC(a, factor):
    gamma = Quant(params['economics']['MAC']['gamma'], 'currency_unit/emissionsrate_unit')
    beta = params['economics']['MAC']['beta']
    return gamma * factor * a**(beta+1) / (beta+1)



def damage_fct(T, T0=None):
    """Quadratic damage function

    T: temperature
    T0 [None]: if specified, substracts damage at T0
    """
    coeff = params['economics']['damages']['coeff']
    dmg = coeff * T**2
    if T0 is not None:
        dmg -= coeff * T0**2
    return dmg