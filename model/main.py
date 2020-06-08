### Import packages

import numpy as np

from pyomo.environ import *
from pyomo.dae import *

from model.common import data, utils, units, economics
from model.export.plot import full_plot
from model.export.save import save_output

utils.tick('Abstract model creation')
from model.abstract_model import m as abstract_model


# Util to create a None-indexed dictionary for scalar components
# (see https://pyomo.readthedocs.io/en/stable/working_abstractmodels/data/raw_dicts.html)
v = lambda val: {None: val} 



class MIMOSA: 

    def __init__(self, params):
        self.params = params
        self.regions = params['regions']
        self.quant = units.Quantity(params)

        self.m = self.create_instance()
        self.discretize()


    @utils.timer('Concrete model creation')
    def create_instance(self):
        
        # Create the data store
        self.data_store = data.DataStore(self.params, self.quant)

        # The data functions need to be changed in the abstract model
        # before initialization. 
        abstract_model.baseline    = lambda t, region: self.data_store.interp_data(t, region, 'baseline')
        abstract_model.population  = lambda t, region: self.data_store.interp_data(t, region, 'population')
        abstract_model.GDP         = lambda t, region: self.data_store.interp_data(t, region, 'GDP')
        abstract_model.TFP         = lambda t, region: self.data_store.interp_data(t, region, 'TFP')

        quant  = self.quant
        params = self.params

        instance_data = {None: {
            'beginyear':        v(params['time']['start']),
            'endyear':          v(params['time']['end']),
            'dt':               v(params['time']['dt']),
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

            'damage_factor':    {r: self.regions[r].get('damage factor', 1) for r in self.regions},
            'damage_coeff':     v(params['economics']['damages']['coeff']),
            'MAC_gamma':        v(quant(params['economics']['MAC']['gamma'], 'currency_unit/emissionsrate_unit')),
            'MAC_beta':         v(params['economics']['MAC']['beta']),

            'init_capitalstock': {r: quant(self.regions[r]['initial capital'], 'currency_unit') for r in self.regions},
            'alpha':            v(params['economics']['GDP']['alpha']),
            'dk':               v(params['economics']['GDP']['depreciation of capital']),
            'sr':               v(params['economics']['GDP']['savings rate']),
            'elasmu':           v(params['economics']['elasmu']),
            'PRTP':             v(params['economics']['PRTP'])
        }}

        m = abstract_model.create_instance(instance_data)
        return m
    

    @utils.timer('Time discretisation')
    def discretize(self):

        num_steps = int(self.m.tf/self.params['time']['dt'])
        discretizer = TransformationFactory('dae.finite_difference')
        discretizer.apply_to(self.m, nfe=num_steps, scheme='BACKWARD')

        # discretizer = TransformationFactory('dae.collocation')
        # discretizer.apply_to(m, nfe=6, ncp=7, scheme='LAGRANGE-RADAU')


    @utils.timer('Model solve')
    def solve(self):
        # solver_manager = SolverManagerFactory('neos')
        # results = solver_manager.solve(m, opt='ipopt')
        results = SolverFactory('ipopt').solve(self.m)

        print('Final NPV:', value(self.m.NPV[self.m.tf]))

    @utils.timer('Plotting results')
    def plot(self, filename='result'):
        full_plot(self.m, filename)

    def save(self, experiment=None, **kwargs):
        save_output(self.params, self.m, experiment, **kwargs)






# consumption_loss = [
#     (value(m.baseline_consumption_NPV[m.year2100,r]) - value(m.consumption_NPV[m.year2100, r])) / value(m.baseline_consumption_NPV[m.year2100,r])
#     for r in regions
# ]
# relative_carbonbudget = [value(m.cumulative_emissions[m.year2100]) / m.baseline_cumulative(value(m.year2100), r) for r in regions]
# print('\nConsumption loss NPV:', consumption_loss)
# print('Relative carbon budget:', relative_carbonbudget)
# print(m.t[m.year2100])

