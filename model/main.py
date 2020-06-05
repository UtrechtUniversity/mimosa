### Import packages

import numpy as np

from pyomo.environ import *
from pyomo.dae import *

from model.common import data, utils, units, economics
from model.common.config import params
from model.visualisation.plot import full_plot

utils.tick('Abstract model creation')
from model.abstract_model import m as abstract_model



# Obtain data from data store
utils.tick('Concrete model creation')
quant = units.Quantity(params)
data_store = data.DataStore(params, quant)

regions = params['regions']

# The data functions need to be changed in the abstract model
# before initialization. 
abstract_model.baseline    = lambda t, region: data_store.interp_data(t, region, 'baseline')
abstract_model.population  = lambda t, region: data_store.interp_data(t, region, 'population')
abstract_model.GDP         = lambda t, region: data_store.interp_data(t, region, 'GDP')
abstract_model.TFP         = lambda t, region: data_store.interp_data(t, region, 'TFP')


# Util to create a None-indexed dictionary for scalar components
# (see https://pyomo.readthedocs.io/en/stable/working_abstractmodels/data/raw_dicts.html)
v = lambda val: {None: val} 

instance_data = {None: {
    'beginyear':        v(params['time']['start']),
    'endyear':          v(params['time']['end']),
    'regions':          v(params['regions'].keys()),
    
    'budget':           v(quant(params['emissions']['carbonbudget'], 'emissions_unit')),
    'inertia_regional': v(params['emissions']['inertia']['regional']),
    'inertia_global':   v(params['emissions']['inertia']['global']),
    'min_level':        v(quant(params['emissions']['min level'], 'emissionsrate_unit')),

    'T0':               v(quant(params['temperature']['initial'], 'temperature_unit')),
    'TCRE':             v(quant(params['temperature']['TCRE'], '(temperature_unit)/(emissions_unit)')),

    'LBD_rate':         v(params['economics']['MAC']['rho']),
    'LBD_scaling':      v(quant('40 GtCO2', 'emissions_unit')),
    'LOT_rate':         v(0),

    'damage_factor':    {r: regions[r].get('damage factor', 1) for r in regions},
    'damage_coeff':     v(params['economics']['damages']['coeff']),
    'MAC_gamma':        v(quant(params['economics']['MAC']['gamma'], 'currency_unit/emissionsrate_unit')),
    'MAC_beta':         v(params['economics']['MAC']['beta']),

    'init_capitalstock': {r: quant(regions[r]['initial capital'], 'currency_unit') for r in regions},
    'alpha':            v(params['economics']['GDP']['alpha']),
    'dk':               v(params['economics']['GDP']['depreciation of capital']),
    'sr':               v(params['economics']['GDP']['savings rate']),
    'elasmu':           v(params['economics']['elasmu']),
    'PRTP':             v(params['economics']['PRTP'])
}}

m = abstract_model.create_instance(instance_data)




utils.tick('Time discretisation')
discretizer = TransformationFactory('dae.finite_difference')
discretizer.apply_to(m, nfe=int(m.tf/params['time']['dt']), scheme='BACKWARD')
# discretizer = TransformationFactory('dae.collocation')
# discretizer.apply_to(m, nfe=6, ncp=7, scheme='LAGRANGE-RADAU')


utils.tick('Model solve')
# solver_manager = SolverManagerFactory('neos')
# results = solver_manager.solve(m, opt='ipopt')
results = SolverFactory('ipopt').solve(m)

print('Final NPV:', value(m.NPV[m.tf]))


# consumption_loss = [
#     (value(m.baseline_consumption_NPV[m.year2100,r]) - value(m.consumption_NPV[m.year2100, r])) / value(m.baseline_consumption_NPV[m.year2100,r])
#     for r in regions
# ]
# relative_carbonbudget = [value(m.cumulative_emissions[m.year2100]) / m.baseline_cumulative(value(m.year2100), r) for r in regions]
# print('\nConsumption loss NPV:', consumption_loss)
# print('Relative carbon budget:', relative_carbonbudget)
# print(m.t[m.year2100])

utils.tick('Plotting results')
full_plot(m)
utils.tick()