### Import packages

import numpy as np
import time as timer

from pyomo.environ import *
from pyomo.dae import *

from model.common import data, utils, economics
from model.common.units import Quant
from model.common.config import params
from model.visualisation.plot import full_plot


m = ConcreteModel()


######################
# Create data (move this to other file)
######################

regions = params['regions']

data_years = np.arange(2015, 2201, 1.0)
SSP = params['SSP']
data_baseline   = {region: data.get_data(data_years, region, SSP, 'emissions', 'emissionsrate_unit')['values'] for region in regions}
data_GDP        = {region: data.get_data(data_years, region, SSP, 'GDP', 'currency_unit')['values'] for region in regions}
data_population = {region: data.get_data(data_years, region, SSP, 'population', 'population_unit')['values'] for region in regions}
data_TFP        = {region: economics.get_TFP(data_years, region) for region in regions}
def get_data(year, region, data_param):
    return np.interp(year, data_years, data_param[region])

m.baseline    = lambda year, region: get_data(year, region, data_baseline)
m.population  = lambda year, region: get_data(year, region, data_population)
m.TFP         = lambda year, region: get_data(year, region, data_TFP)
m.GDP         = lambda year, region: get_data(year, region, data_GDP)
def baseline_cumulative(beginyear, endyear, region):
    newyears = np.linspace(beginyear, endyear, 100)
    return np.trapz(m.baseline(newyears, region), x=newyears)
m.baseline_cumulative = baseline_cumulative


######################
# Create model
######################

m.beginyear = params['time']['start']
m.endyear = params['time']['end']
m.tf = m.endyear - m.beginyear
m.year2100 = 2100 - m.beginyear
m.t = ContinuousSet(bounds=(0, m.tf), initialize=[m.year2100])

m.regions = Set(initialize=regions.keys())


### TODO: Maybe add initialize

## Global variables
m.temperature = Var(m.t)
m.cumulative_emissions = Var(m.t, initialize=0)
m.global_emissions = Var(m.t)
m.NPV = Var(m.t)

## Regional variables
# Control variable:
m.relative_abatement = Var(m.t, m.regions, initialize=0, bounds=(0, 2))
# State variables:
m.init_capitalstock = Param(m.regions, initialize={region: Quant(regions[region]['initial capital'], 'currency_unit') for region in regions})
# TODO: Bounds should be different for each region
# m.capital_stock = Var(m.t, bounds=(0.2 * GDP(m.beginyear, 'World'), 3 * GDP(m.endyear, 'World')), initialize=init_capitalstock)
m.capital_stock = Var(m.t, m.regions, initialize=lambda m,t,r: m.init_capitalstock[r])
m.regional_emissions = Var(m.t, m.regions)

## Derivatives
m.cumulative_emissionsdot = DerivativeVar(m.cumulative_emissions, wrt=m.t)
m.global_emissionsdot = DerivativeVar(m.global_emissions, wrt=m.t)
m.NPVdot = DerivativeVar(m.NPV, wrt=m.t)
m.capital_stockdot = DerivativeVar(m.capital_stock, wrt=m.t)
m.regional_emissionsdot = DerivativeVar(m.regional_emissions, wrt=m.t)

## Constraints
global_constraints = []
regional_constraints = []



######################
# Emission equations
######################

regional_constraints.append(lambda m,t,r: m.regional_emissions[t, r] == (1-m.relative_abatement[t, r]) * m.baseline(m.beginyear+t, r))
global_constraints.append(lambda m,t: m.global_emissions[t] == sum(m.regional_emissions[t, r] for r in m.regions))
global_constraints.append(lambda m,t: m.cumulative_emissionsdot[t] == m.global_emissions[t])

m.T0 = Param(initialize=Quant(params['temperature']['initial'], 'temperature_unit'))
m.TCRE = Param(initialize=Quant(params['temperature']['TCRE'], '(temperature_unit)/(emissions_unit)'))
global_constraints.append(lambda m,t: m.temperature[t] == m.T0 + m.TCRE * m.cumulative_emissions[t])

# Emission constraints

carbonbudget = params['emissions']['carbonbudget']
if carbonbudget is not False:
    budget = Quant(carbonbudget, 'emissions_unit')
    global_constraints.append(lambda m,t: (m.cumulative_emissions[t] - budget <= 0) if t >= m.year2100 else Constraint.Skip)

inertia_regional = params['emissions']['inertia']['regional']
if inertia_regional is not False:
    regional_constraints.append(lambda m,t,r: m.regional_emissionsdot[t, r] >= inertia_regional * m.baseline(m.beginyear, r))

inertia_global = params['emissions']['inertia']['global']
if inertia_global is not False:
    global_constraints.append(lambda m,t: m.global_emissionsdot[t] >= inertia_global * sum(m.baseline(m.beginyear, r) for r in m.regions)) # TODO global baseline

min_level = params['emissions']['min level']
if min_level is not False:
    global_constraints.append(lambda m,t: m.global_emissions[t] >= Quant(min_level, 'emissionsrate_unit'))



######################
# Abatement and damage costs
######################


### Technological learning
m.LBD_rate = Param(initialize=params['economics']['MAC']['rho'])
m.log_LBD_rate = Param(initialize=log(m.LBD_rate) / log(2))
m.LBD_factor = Var(m.t)
m.learning_factor = Var(m.t)
LBD_scaling = Quant('40 GtCO2', 'emissions_unit')
global_constraints.append(lambda m,t:
    m.LBD_factor[t] == ((sum(m.baseline_cumulative(m.beginyear, m.beginyear+t, r) for r in m.regions) - m.cumulative_emissions[t])/LBD_scaling+1.0)**m.log_LBD_rate)

m.LOT_rate = Param(initialize=0)
m.LOT_factor = Var(m.t)
global_constraints.append(lambda m,t: m.LOT_factor[t] == 1 / (1+m.LOT_rate)**t)

global_constraints.append(lambda m,t: m.learning_factor[t] == (m.LBD_factor[t] * m.LOT_factor[t]))

m.damage_costs = Var(m.t, m.regions)
m.abatement_costs = Var(m.t, m.regions)
m.carbonprice = Var(m.t, m.regions)

m.damage_factor = Param(m.regions, initialize={r: regions[r].get('damage factor', 1) for r in regions})
m.damage_coeff = Param(initialize=params['economics']['damages']['coeff'])
m.MAC_gamma = Param(initialize=Quant(params['economics']['MAC']['gamma'], 'currency_unit/emissionsrate_unit'))
m.MAC_beta = Param(initialize=params['economics']['MAC']['beta']) # TODO Maybe move these params to economics.MAC/AC by including "m"

regional_constraints.extend([
    lambda m,t,r: m.damage_costs[t,r] == m.damage_factor[r] * economics.damage_fct(m.temperature[t], m.damage_coeff, m.T0),
    lambda m,t,r: m.abatement_costs[t,r] == economics.AC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta) * m.baseline(m.beginyear+t, r),
    lambda m,t,r: m.carbonprice[t,r] == economics.MAC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta)
])



######################
# Cobb-Douglas (move this to other file)
######################

# Parameters
m.alpha = Param(initialize=params['economics']['GDP']['alpha'])
m.dk = Param(initialize=params['economics']['GDP']['depreciation of capital'])
m.sr = Param(initialize=params['economics']['GDP']['savings rate'])
m.elasmu = Param(initialize=params['economics']['elasmu'])

m.GDP_gross = Var(m.t, m.regions)
m.GDP_net = Var(m.t, m.regions)
m.investments = Var(m.t, m.regions)
m.consumption = Var(m.t, m.regions, initialize=(1-m.sr)*m.GDP(m.beginyear, utils.firstk(regions)))
m.utility = Var(m.t, m.regions)
m.L = lambda t,r: m.population(m.beginyear+t, r)

regional_constraints.extend([
    lambda m,t,r: m.GDP_gross[t,r] == economics.calc_GDP(m.TFP(m.beginyear+t, r), m.L(t,r), m.capital_stock[t,r], m.alpha),
    lambda m,t,r: m.GDP_net[t,r] == m.GDP_gross[t,r] * (1-m.damage_costs[t,r]) - m.abatement_costs[t,r],
    lambda m,t,r: m.investments[t,r] == m.sr * m.GDP_net[t,r],
    lambda m,t,r: m.consumption[t,r] == (1-m.sr) * m.GDP_net[t,r],
    lambda m,t,r: m.utility[t,r] == m.L(t,r) * ( (m.consumption[t,r] / m.L(t,r)) ** (1-m.elasmu) - 1 ) / (1-m.elasmu),
    lambda m,t,r: m.capital_stockdot[t,r] == np.log(1-m.dk) * m.capital_stock[t,r] + m.investments[t,r]
])

m.consumption_NPV = Var(m.t, m.regions)
m.consumption_NPVdot = DerivativeVar(m.consumption_NPV, wrt=m.t)
m.baseline_consumption_NPV = Var(m.t, m.regions)
m.baseline_consumption_NPVdot = DerivativeVar(m.baseline_consumption_NPV, wrt=m.t)
m.baseline_consumption = lambda t,r: (1-m.sr) * m.GDP(m.beginyear+t, r)
regional_constraints.extend([
    lambda m,t,r: m.consumption_NPVdot[t,r] == exp(-0.05 * t) * m.consumption[t,r],
    lambda m,t,r: m.baseline_consumption_NPVdot[t,r] == exp(-0.05 * t) * m.baseline_consumption(t,r)
])




######################
# Optimisation
######################

m.PRTP = Param(initialize=params['economics']['PRTP'])
global_constraints.append(lambda m,t: m.NPVdot[t] == exp(-m.PRTP * t) * sum(m.utility[t,r] for r in m.regions))


def _init(m):
    yield m.temperature[0] == m.T0
    for r in m.regions:
        yield m.regional_emissions[0,r] == m.baseline(m.beginyear, r)
        yield m.capital_stock[0,r] == m.init_capitalstock[r]
        yield m.carbonprice[0,r] == 0
        yield m.consumption_NPV[0,r] == 0
        yield m.baseline_consumption_NPV[0,r] == 0
    yield m.global_emissions[0] == sum(m.baseline(m.beginyear, r) for r in m.regions)
    yield m.cumulative_emissions[0] == 0
    yield m.NPV[0] == 0
m.init = ConstraintList(rule=_init)
    
for fct in global_constraints:
    utils.add_constraint(m, Constraint(m.t, rule=fct))
for fct in regional_constraints:
    utils.add_constraint(m, Constraint(m.t, m.regions, rule=fct))

m.obj = Objective(expr=m.NPV[m.tf], sense=maximize)


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
consumption_loss = [
    (value(m.baseline_consumption_NPV[m.year2100,r]) - value(m.consumption_NPV[m.year2100, r])) / value(m.baseline_consumption_NPV[m.year2100,r])
    for r in regions
]
relative_carbonbudget = [value(m.cumulative_emissions[m.year2100]) / m.baseline_cumulative(m.beginyear, 2100, r) for r in regions]
print('\nConsumption loss NPV:', consumption_loss)
print('Relative carbon budget:', relative_carbonbudget)
print(m.t[m.year2100])

full_plot(m, m.baseline)
# TODO make sure 'baseline' is also accessible from plot