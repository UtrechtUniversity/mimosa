### Import packages

import numpy as np
import time as timer

from pyomo.environ import *
from pyomo.dae import *

from model.common import data, utils, economics
from model.common.units import Quant
from model.common.config import params
from model.visualisation.plot import full_plot

from model import abstract_model





### Add data functions
# Move this first part other Data-file
regions = params['regions']
data_years = np.arange(2015, 2201, 1.0)
SSP = params['SSP']
data_baseline   = {region: data.get_data(data_years, region, SSP, 'emissions', 'emissionsrate_unit')['values'] for region in regions}
data_GDP        = {region: data.get_data(data_years, region, SSP, 'GDP', 'currency_unit')['values'] for region in regions}
data_population = {region: data.get_data(data_years, region, SSP, 'population', 'population_unit')['values'] for region in regions}
data_TFP        = {region: economics.get_TFP(data_years, region) for region in regions}
def get_data(t, region, data_param):
    year = params['time']['start'] + t
    return np.interp(year, data_years, data_param[region])

# The data functions need to be changed in the abstract model
# before initialization. 
abstract_model.m.baseline    = lambda t, region: get_data(t, region, data_baseline)
abstract_model.m.population  = lambda t, region: get_data(t, region, data_population)
abstract_model.m.TFP         = lambda t, region: get_data(t, region, data_TFP)
abstract_model.m.GDP         = lambda t, region: get_data(t, region, data_GDP)






# Util to create a None-indexed dictionary for un-indexed Params
v = lambda val: {None: val} 

instance_data = {None: {
    'beginyear': v(params['time']['start']),
    'endyear': v(params['time']['end']),

    'regions': v(params['regions'].keys()),

    'init_capitalstock': {region: Quant(regions[region]['initial capital'], 'currency_unit') for region in regions},

    'T0': v(Quant(params['temperature']['initial'], 'temperature_unit')),
    'TCRE': v(Quant(params['temperature']['TCRE'], '(temperature_unit)/(emissions_unit)')),
    
    'budget': v(Quant(params['emissions']['carbonbudget'], 'emissions_unit')),
    'inertia_regional': v(params['emissions']['inertia']['regional']),
    'inertia_global': v(params['emissions']['inertia']['global']),
    'min_level': v(Quant(params['emissions']['min level'], 'emissionsrate_unit')),

    'LBD_rate': v(params['economics']['MAC']['rho']),
    'LBD_scaling': v(Quant('40 GtCO2', 'emissions_unit')),
    'LOT_rate': v(0),

    'damage_factor': {r: regions[r].get('damage factor', 1) for r in regions},
    'damage_coeff': v(params['economics']['damages']['coeff']),
    'MAC_gamma': v(Quant(params['economics']['MAC']['gamma'], 'currency_unit/emissionsrate_unit')),
    'MAC_beta': v(params['economics']['MAC']['beta']),

    'alpha': v(params['economics']['GDP']['alpha']),
    'dk': v(params['economics']['GDP']['depreciation of capital']),
    'sr': v(params['economics']['GDP']['savings rate']),
    'elasmu': v(params['economics']['elasmu']),

    'PRTP': v(params['economics']['PRTP'])
}}

m = abstract_model.m.create_instance(instance_data)




timer_0 = timer.time()
discretizer = TransformationFactory('dae.finite_difference')
discretizer.apply_to(m, nfe=int(m.tf/params['time']['dt']), scheme='BACKWARD')
# discretizer = TransformationFactory('dae.collocation')
# discretizer.apply_to(m, nfe=6, ncp=7, scheme='LAGRANGE-RADAU')
timer_1 = timer.time()
print('Discretisation took {} seconds'.format(timer_1-timer_0))


print("Starting solve.")
# solver_manager = SolverManagerFactory('neos')
# results = solver_manager.solve(m, opt='ipopt')
results = SolverFactory('ipopt').solve(m)
timer_2 = timer.time()
print('Solving took {} seconds'.format(timer_2-timer_1))

print('Final NPV:', value(m.NPV[m.tf]))
# consumption_loss = [
#     (value(m.baseline_consumption_NPV[m.year2100,r]) - value(m.consumption_NPV[m.year2100, r])) / value(m.baseline_consumption_NPV[m.year2100,r])
#     for r in regions
# ]
# relative_carbonbudget = [value(m.cumulative_emissions[m.year2100]) / m.baseline_cumulative(value(m.year2100), r) for r in regions]
# print('\nConsumption loss NPV:', consumption_loss)
# print('Relative carbon budget:', relative_carbonbudget)
# print(m.t[m.year2100])

full_plot(m, m.baseline)
# TODO make sure 'baseline' is also accessible from plot