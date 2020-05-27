### Import packages

import numpy as np
import time as timer
from gekko import GEKKO

from model.common.config import params
from model.common.units import Quant
from model.common import utils, data
from model.components import economics, emissions, time, variable_factory
from model.visualisation import plot

m = GEKKO(remote=params['GEKKO']['remote'])
m.options.IMODE = params['GEKKO']['imode']
m.options.MAX_ITER = params['GEKKO']['max_iter']



######################
# Regions and time
######################

regions = params['regions']
regions_i = range(len(regions))
years, masks = time.create_time(m)



######################
# Initialise variables
# (create objects, add initial value and lower/upper bounds)
######################

## Exogenous variables (parameters)
m.baseline_emissions, m.baseline_cumulative = variable_factory.create_baseline_array(m, regions, years)
m.final_baseline_cumulative = utils.total_at_t(m.baseline_cumulative, -1)
m.TFP                   = variable_factory.create_TFP_array(m, regions, years)
m.L                     = variable_factory.create_population_array(m, regions, years)

## Global variables
m.temperature           = variable_factory.create_temperature(m, m.final_baseline_cumulative)
m.cumulative_emissions  = variable_factory.create_cumulative_emissions(m, m.final_baseline_cumulative)
m.global_emissions      = variable_factory.create_global_emissions(m, regions, m.baseline_emissions)
m.NPV                   = variable_factory.create_NPV(m)

## Regional variables
# Control variable:
m.relative_abatement    = variable_factory.create_relative_abatement(m, regions)
# State variables:
m.capital_stock         = variable_factory.create_capital_stock(m, regions, years)
m.regional_emissions    = variable_factory.create_regional_emissions(m, regions, m.baseline_emissions)



######################
# Emission equations
######################

m.Equations([m.regional_emissions[i] == (1-m.relative_abatement[i]) * m.baseline_emissions[i] for i in regions_i])
m.Equation(m.global_emissions == sum(m.regional_emissions))
m.Equation(m.cumulative_emissions.dt() == m.global_emissions)

T0 = params['temperature']['initial']
TCRE = params['temperature']['TCRE']
m.Equation(m.temperature == T0 + TCRE * m.cumulative_emissions)


## Constraints

carbonbudget = params['emissions']['carbonbudget']
if carbonbudget is not False:
    m.Equation( masks['after_2100'] * (m.cumulative_emissions - Quant(carbonbudget, 'emissions_unit')) <= 0 )

inertia_regional = params['emissions']['inertia']['regional']
if inertia_regional is not False:
    m.Equations([ m.regional_emissions[i].dt() >= inertia_regional * m.baseline_emissions[i][0] for i in regions_i ])

inertia_global = params['emissions']['inertia']['global']
if inertia_global is not False:
    m.Equation( m.global_emissions.dt() >= inertia_global * utils.total_at_t(m.baseline_emissions) )

min_level = params['emissions']['min level']
if min_level is not False:
    m.Equation( m.global_emissions >= Quant(min_level, 'emissionsrate_unit') )



######################
# Abatement and damage costs
######################


### Technological learning
m.global_cumulative_baseline = m.Intermediate(sum(m.baseline_cumulative))
LBD_scaling = Quant('40 GtCO2', 'emissions_unit')
m.LBD_factor = m.Intermediate(
    ((m.global_cumulative_baseline - m.cumulative_emissions) / LBD_scaling + 1.0) ** np.log2(params['economics']['MAC']['rho'])
)

m.damage_costs = [None]*len(regions)
m.abatement_costs = [None]*len(regions)
m.carbonprice = [None]*len(regions)

for i, region in enumerate(regions):
    m.damage_costs[i]       = m.Intermediate( economics.damage_fct(m.temperature) - economics.damage_fct(T0) )
    m.abatement_costs[i]    = m.Intermediate( economics.AC(m.relative_abatement[i], m.LBD_factor) * m.baseline_emissions[i] ) 
    m.carbonprice[i]        = m.Intermediate( economics.MAC(m.relative_abatement[i], m.LBD_factor) )



######################
# Cobb-Douglas (move this to other file)
######################

# Parameters
alpha = params['economics']['GDP']['alpha']
dk = params['economics']['GDP']['depreciation of capital']
sr = params['economics']['GDP']['savings rate']
elasmu = params['economics']['elasmu']

m.GDP_gross = [None]*len(regions)
m.GDP_net = [None]*len(regions)
m.investments = [None]*len(regions)
m.consumption = [None]*len(regions)
m.utility = [None]*len(regions)

for i, region in enumerate(regions):
    m.GDP_gross[i]      = m.Intermediate(economics.calc_GDP(m.TFP[i], m.L[i], m.capital_stock[i], alpha))
    m.GDP_net[i]        = m.Intermediate(m.GDP_gross[i] * (1-m.damage_costs[i]) - m.abatement_costs[i])
    m.Equation(m.GDP_net[i] > 0)
    m.investments[i]    = m.Intermediate(sr * m.GDP_net[i])
    m.consumption[i]    = m.Intermediate((1-sr) * m.GDP_net[i])

    m.utility[i] = m.Intermediate(
        m.L[i] * ( (m.consumption[i] / m.L[i]) ** (1-elasmu) - 1 ) / (1-elasmu)
    )

    m.Equation(m.capital_stock[i].dt() == np.log(1-dk) * m.capital_stock[i] + m.investments[i])



######################
# Optimisation
######################

# Calculate total discounted utility
r = params['economics']['PRTP']
m.Equation(m.NPV.dt() == m.exp(-r * m.t) * sum(m.utility))


# Objective function
m.Maximize(masks['final'] * m.NPV)

# Solve
timer_0 = timer.time()
m.solve(debug=0, disp=params['GEKKO']['verbose'], GUI=False)
timer_1 = timer.time()

if m.options.SOLVESTATUS:
    print("Succeeded in finding optimal solution.")
else:
    print("Optimal solution NOT found.")
print('Took {} seconds'.format(timer_1-timer_0))

# Create plot
plot.full_plot(m, regions, years)