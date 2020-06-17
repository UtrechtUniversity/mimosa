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
from model.components import emissions, damages, abatement, cobbdouglas


######################
# Create model
######################

m = AbstractModel()

## Constraints
# Each global / regional constraint will be put in these lists,
# then added to the model at the end of this file.
global_constraints = []
regional_constraints = []


## Time and region
m.beginyear     = Param()
m.endyear       = Param()
m.tf            = Param(initialize=m.endyear - m.beginyear)
m.year2100      = Param(initialize=2100 - m.beginyear)
m.t             = ContinuousSet(bounds=(0, m.tf))

m.regions = Set(ordered=True)


######################
# Create data functions
# Will be initialised when creating a concrete instance of the model
######################

m.baseline      = None
m.population    = None
m.TFP           = None
m.GDP           = None
def baseline_cumulative(t_end, region):
    t_values = np.linspace(0, t_end, 100)
    return np.trapz(m.baseline(t_values, region), x=t_values)
m.baseline_cumulative = baseline_cumulative


######################
# Components
######################

# Emissions and temperature equations
emissions_reg, emissions_glob = emissions.constraints(m)
regional_constraints.extend(emissions_reg)
global_constraints.extend(emissions_glob)


# Damage costs
damages_reg, damages_glob = damages.constraints(m)
regional_constraints.extend(damages_reg)
global_constraints.extend(damages_glob)


# Abatement costs
abatement_reg, abatement_glob = abatement.constraints(m)
regional_constraints.extend(abatement_reg)
global_constraints.extend(abatement_glob)


# Cobb-Douglas and economics
cobbdouglas_reg, cobbdouglas_glob = cobbdouglas.constraints(m)
regional_constraints.extend(cobbdouglas_reg)
global_constraints.extend(cobbdouglas_glob)




######################
# Optimisation
######################

m.NPV = Var(m.t)
m.NPVdot = DerivativeVar(m.NPV, wrt=m.t)
m.PRTP = Param()
global_constraints.append(lambda m,t: m.NPVdot[t] == exp(-m.PRTP * t) * sum(m.L(t,r) * m.utility[t,r] for r in m.regions))


def _init(m):
    yield m.temperature[0] == m.T0
    for r in m.regions:
        yield m.regional_emissions[0,r] == m.baseline(0, r)
        yield m.capital_stock[0,r] == m.init_capitalstock[r]
        yield m.carbonprice[0,r] == 0
        yield m.adapt_level[0,r] == m.adapt_curr_level
        yield m.gross_damages[0,r] == 0
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