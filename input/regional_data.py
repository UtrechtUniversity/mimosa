import numpy as np
import pandas as pd

AD_RICE_coeffs = pd.DataFrame({
    'AFRICA': {'a1': 0, 'a2': 0.0198, 'a3': 1.233, 'g1': 0.2897, 'g2': 3.7589},
    'CHINA': {'a1': -0.0029, 'a2': 0.00130, 'a3': 2.37080, 'g1': 0.55910, 'g2': 9.69100},
    'EUROPE': {'a1': 0, 'a2': 0.00470, 'a3': 2.76940, 'g1': 0.05440, 'g2': 4.4843},
    'HIO': {'a1': 0, 'a2': 0.00580, 'a3': 1.95120, 'g1': 0.02460, 'g2': 2.72710},
    'INDIA': {'a1': 0, 'a2': 0.01300, 'a3': 1.7239, 'g1': 0.2230, 'g2': 3.1357},
    'JAPAN': {'a1': -0.00190, 'a2': 0.00050, 'a3': 3.53540, 'g1': 0.00920, 'g2': 3.16830},
    'LI': {'a1': 0, 'a2': 0.00890, 'a3': 1.87040, 'g1': 0.04220, 'g2': 2.49510},
    'LMI': {'a1': 0, 'a2': 0.00470, 'a3': 1.90260, 'g1': 0.05270, 'g2': 2.35240},
    'MI': {'a1': 0, 'a2': 0.00640, 'a3': 1.67060, 'g1': 0.04770, 'g2': 3.92940},
    'USA': {'a1': -0.00120, 'a2': 0.00050, 'a3': 3.34310, 'g1': 0.03770, 'g2': 6.84460}
}).T

SSP_to_RICE_regions = {
    'R5.2OECD': ['USA', 'JAPAN', 'EUROPE'],
    'R5.2ASIA': ['CHINA', 'INDIA', 'LI'],
    'R5.2LAM': ['LMI'],
    'R5.2MAF': ['AFRICA', 'HIO'],
    'R5.2REF': [],
}

def get_damage_adapt_coeffs(region, param_name):
    RICE_regions = SSP_to_RICE_regions[region]
    if len(RICE_regions) == 0:
        return 0.0 if param_name not in ['a3', 'g2'] else 1
    # TODO: current aggregation is "mean". Maybe population/GDP weighted is better
    coeffs = AD_RICE_coeffs.loc[RICE_regions].mean()
    return float(coeffs[param_name])


def get_param_value(region, params):
    if params[0] == 'damages':
        # Get (damages, a1), ..., (damages, a3)
        return get_damage_adapt_coeffs(region, params[1])
    if params[0] == 'adaptation':
        # Get (adaptation, g1), (adaptation, g2)
        return get_damage_adapt_coeffs(region, params[1])
    raise Exception('{} not found for region {}'.format(region, params))
    


# damage_coeffs = {
#     'DICE': [0, 0.267],
#     'Global': np.array([0.0018, 0.0023]) * 100,
#     'US': [0.0, 0.1414],
#     'EU': [0.0, 0.1591],
#     'Japan': [0.0, 0.1617],
#     'Russia': [0.0, 0.1151],
#     'Eurasia': [0.0, 0.1305],
#     'China': [0.0785, 0.1259],
#     'India': [0.4385, 0.1689],
#     'Middle East': [0.277989, 0.1586],
#     'Africa': [0.340974, 0.1983],
#     'Latin America': [0.0609, 0.1345],
#     'OHI': [0.0, 0.1564],
#     'Other non-OECD Asia': [0.1755, 0.1734]
# }