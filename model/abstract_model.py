##############################################
# Abstract representation of the model
# --------------------------------------------
# Contains all model equations and constraints
#
##############################################

import numpy as np
from model.common import utils, economics
from model.common.pyomo import *
from model.components import emissions, abatement, cobbdouglas, damages


######################
# Create model
######################

def create_abstract_model(damage_module='RICE'):

    m = AbstractModel()

    ## Constraints
    # Each constraint will be put in this list,
    # then added to the model at the end of this file.
    constraints = []


    ## Time and region
    m.beginyear     = Param()
    m.dt            = Param()
    m.tf            = Param()
    m.t             = Set()
    m.year          = None  # Initialised with concrete instance
    m.year2100      = Param()

    m.regions = Set(ordered=True)


    ######################
    # Create data functions
    # Will be initialised when creating a concrete instance of the model
    ######################

    m.baseline_emissions    = None
    m.population            = None
    m.TFP                   = None
    m.GDP                   = None
    m.carbon_intensity      = None
    def baseline_cumulative(year_start, year_end, region):
        years = np.linspace(year_start, year_end, 100)
        return np.trapz(m.baseline_emissions(years, region), x=years)
    m.baseline_cumulative = baseline_cumulative
    m.baseline_cumulative_global = lambda m, year_start, year_end: sum(baseline_cumulative(year_start, year_end, r) for r in m.regions)


    ######################
    # Components
    ######################

    # Emissions and temperature equations
    constraints.extend(emissions.constraints(m))


    # Damage costs
    if damage_module == 'RICE2010':
        constraints.extend(damages.AD_RICE2010.constraints(m))
    elif damage_module == 'WITCH':
        constraints.extend(damages.AD_WITCH.constraints(m))
    elif damage_module == 'RICE2012':
        constraints.extend(damages.AD_RICE2012.constraints(m))
    elif damage_module == 'nodamage':
        constraints.extend(damages.nodamage.constraints(m))
    else:
        raise NotImplementedError


    # Abatement costs
    constraints.extend(abatement.constraints(m))


    # Cobb-Douglas and economics
    constraints.extend(cobbdouglas.constraints(m))




    ######################
    # Optimisation
    ######################

    m.NPV = Var(m.t)
    m.PRTP = Param()
    constraints.extend([
        GlobalConstraint(
            lambda m,t: m.NPV[t] == m.NPV[t-1] + m.dt * exp(-m.PRTP * (m.year(t) - m.beginyear)) * sum(m.L(m.year(t),r) * m.utility[t,r] for r in m.regions) 
            if t > 0 else Constraint.Skip,
            name='NPV'
        ),
        GlobalInitConstraint(lambda m: m.NPV[0] == 0)
    ])
    
    for constraint in constraints:
        utils.add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)

    m.obj = Objective(rule=lambda m: m.NPV[m.tf], sense=maximize)
    # m.obj = Objective(rule=lambda m: m.NPV[m.tf] * (
    #     soft_switch(m.budget-(
    #         m.cumulative_emissions[m.year2100]
    #         + sum(soft_min(m.global_emissions[t]) for t in m.t if m.year(t) >= 2100)
    #     ), scale=1)
    # ), sense=maximize)

    return m

def name_and_fct(fct):
    if isinstance(fct, tuple):
        name = fct[1]
        fct = fct[0]
    else:
        name = None
    return name, fct