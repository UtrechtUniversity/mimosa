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

m = abstract_model.m.create_instance({None: {
    'sr': {None: params['economics']['GDP']['savings rate']}
}})




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