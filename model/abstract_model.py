##############################################
# Abstract representation of the model
# --------------------------------------------
# Contains all model equations and constraints
#
##############################################

import numpy as np
from pyomo.environ import *
from pyomo.dae import *

from model.common import utils, economics

m = AbstractModel()


######################
# Create data (move this to other file)
######################

m.baseline    = None
m.population  = None
m.TFP         = None
m.GDP         = None
def baseline_cumulative(t_end, region):
    t_values = np.linspace(0, t_end, 100)
    return np.trapz(m.baseline(t_values, region), x=t_values)
m.baseline_cumulative = baseline_cumulative


######################
# Create model
######################

## Constraints
global_constraints = []
regional_constraints = []

m.beginyear = Param()
m.endyear = Param()
m.tf = Param(initialize=m.endyear - m.beginyear)
m.year2100 = Param(initialize=2100 - m.beginyear)
m.t = ContinuousSet(bounds=(0, m.tf))


m.regions = Set(ordered=True)


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
m.init_capitalstock = Param(m.regions)
m.capital_stock = Var(m.t, m.regions, initialize=lambda m,t,r: m.init_capitalstock[r])
m.regional_emissions = Var(m.t, m.regions)

## Derivatives
m.cumulative_emissionsdot = DerivativeVar(m.cumulative_emissions, wrt=m.t)
m.global_emissionsdot = DerivativeVar(m.global_emissions, wrt=m.t)
m.NPVdot = DerivativeVar(m.NPV, wrt=m.t)
m.capital_stockdot = DerivativeVar(m.capital_stock, wrt=m.t)
m.regional_emissionsdot = DerivativeVar(m.regional_emissions, wrt=m.t)



######################
# Emission equations
######################

regional_constraints.append(lambda m,t,r: m.regional_emissions[t, r] == (1-m.relative_abatement[t, r]) * m.baseline(t, r))
global_constraints.append(lambda m,t: m.global_emissions[t] == sum(m.regional_emissions[t, r] for r in m.regions))
global_constraints.append(lambda m,t: m.cumulative_emissionsdot[t] == m.global_emissions[t])

m.T0 = Param()
m.TCRE = Param()
global_constraints.append(lambda m,t: m.temperature[t] == m.T0 + m.TCRE * m.cumulative_emissions[t])

# Emission constraints

m.budget = Param()
global_constraints.append(lambda m,t: (m.cumulative_emissions[t] - m.budget <= 0) if (t >= m.year2100 and value(m.budget) is not False) else Constraint.Skip)

m.inertia_regional = Param()
regional_constraints.append(lambda m,t,r: m.regional_emissionsdot[t, r] >= m.inertia_regional * m.baseline(0, r) if value(m.inertia_regional) is not False else Constraint.Skip)

m.inertia_global = Param()
global_constraints.append(lambda m,t: m.global_emissionsdot[t] >= m.inertia_global * sum(m.baseline(0, r) for r in m.regions) if value(m.inertia_global) is not False else Constraint.Skip) # TODO global baseline

m.min_level = Param()
global_constraints.append(lambda m,t: m.global_emissions[t] >= m.min_level if value(m.min_level) is not False else Constraint.Skip)



######################
# Abatement and damage costs
######################


### Technological learning
m.LBD_rate = Param()
m.log_LBD_rate = Param(initialize=log(m.LBD_rate) / log(2))
m.LBD_factor = Var(m.t)
m.LBD_scaling = Param()
global_constraints.append(lambda m,t:
    m.LBD_factor[t] == ((sum(m.baseline_cumulative(t, r) for r in m.regions) - m.cumulative_emissions[t])/m.LBD_scaling+1.0)**m.log_LBD_rate)

m.LOT_rate = Param()
m.LOT_factor = Var(m.t)
global_constraints.append(lambda m,t: m.LOT_factor[t] == 1 / (1+m.LOT_rate)**t)

m.learning_factor = Var(m.t)
global_constraints.append(lambda m,t: m.learning_factor[t] == (m.LBD_factor[t] * m.LOT_factor[t]))

m.damage_costs = Var(m.t, m.regions)
m.abatement_costs = Var(m.t, m.regions)
m.carbonprice = Var(m.t, m.regions)

m.damage_factor = Param(m.regions)
m.damage_coeff = Param()
m.MAC_gamma = Param()
m.MAC_beta = Param() # TODO Maybe move these params to economics.MAC/AC by including "m"

regional_constraints.extend([
    lambda m,t,r: m.damage_costs[t,r] == m.damage_factor[r] * economics.damage_fct(m.temperature[t], m.damage_coeff, m.T0),
    lambda m,t,r: m.abatement_costs[t,r] == economics.AC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta) * m.baseline(t, r),
    lambda m,t,r: m.carbonprice[t,r] == economics.MAC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta)
])



######################
# Cobb-Douglas (move this to other file)
######################

# Parameters
m.alpha = Param()
m.dk = Param()
m.sr = Param()
m.elasmu = Param()

m.GDP_gross = Var(m.t, m.regions)
m.GDP_net = Var(m.t, m.regions)
m.investments = Var(m.t, m.regions)
m.consumption = Var(m.t, m.regions, initialize=lambda m: (1-m.sr)*m.GDP(0, m.regions.first()))
m.utility = Var(m.t, m.regions)
m.L = lambda t,r: m.population(t, r)

regional_constraints.extend([
    lambda m,t,r: m.GDP_gross[t,r] == economics.calc_GDP(m.TFP(t, r), m.L(t,r), m.capital_stock[t,r], m.alpha),
    lambda m,t,r: m.GDP_net[t,r] == m.GDP_gross[t,r] * (1-m.damage_costs[t,r]) - m.abatement_costs[t,r],
    lambda m,t,r: m.investments[t,r] == m.sr * m.GDP_net[t,r],
    lambda m,t,r: m.consumption[t,r] == (1-m.sr) * m.GDP_net[t,r],
    lambda m,t,r: m.utility[t,r] == m.L(t,r) * ( (m.consumption[t,r] / m.L(t,r)) ** (1-m.elasmu) - 1 ) / (1-m.elasmu),
    lambda m,t,r: m.capital_stockdot[t,r] == np.log(1-m.dk) * m.capital_stock[t,r] + m.investments[t,r]
])

# m.consumption_NPV = Var(m.t, m.regions)
# m.consumption_NPVdot = DerivativeVar(m.consumption_NPV, wrt=m.t)
# m.baseline_consumption_NPV = Var(m.t, m.regions)
# m.baseline_consumption_NPVdot = DerivativeVar(m.baseline_consumption_NPV, wrt=m.t)
# m.baseline_consumption = lambda t,r: (1-m.sr) * m.GDP(t, r)
# regional_constraints.extend([
#     lambda m,t,r: m.consumption_NPVdot[t,r] == exp(-0.05 * t) * m.consumption[t,r],
#     lambda m,t,r: m.baseline_consumption_NPVdot[t,r] == exp(-0.05 * t) * m.baseline_consumption(t,r)
# ])




######################
# Optimisation
######################

m.PRTP = Param()
global_constraints.append(lambda m,t: m.NPVdot[t] == exp(-m.PRTP * t) * sum(m.utility[t,r] for r in m.regions))


def _init(m):
    yield m.temperature[0] == m.T0
    for r in m.regions:
        yield m.regional_emissions[0,r] == m.baseline(0, r)
        yield m.capital_stock[0,r] == m.init_capitalstock[r]
        yield m.carbonprice[0,r] == 0
        # yield m.consumption_NPV[0,r] == 0
        # yield m.baseline_consumption_NPV[0,r] == 0
    yield m.global_emissions[0] == sum(m.baseline(0, r) for r in m.regions)
    yield m.cumulative_emissions[0] == 0
    yield m.NPV[0] == 0
m.init = ConstraintList(rule=_init)
    
for fct in global_constraints:
    utils.add_constraint(m, Constraint(m.t, rule=fct))
for fct in regional_constraints:
    utils.add_constraint(m, Constraint(m.t, m.regions, rule=fct))

m.obj = Objective(rule=lambda m: m.NPV[m.tf], sense=maximize)