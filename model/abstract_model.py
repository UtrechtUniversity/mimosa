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
    # Each global / regional constraint will be put in these lists,
    # then added to the model at the end of this file.
    global_constraints      = []
    global_constraints_init = []
    regional_constraints    = []
    regional_constraints_init = []


    ## Time and region
    m.beginyear     = Param()
    m.dt            = Param()
    m.tf            = Param()
    m.t             = Set()
    m.year          = None  # Initialised with concrete instance

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


    ######################
    # Components
    ######################

    # Emissions and temperature equations
    c_emissions = emissions.constraints(m)

    global_constraints          .extend(c_emissions['global'])
    global_constraints_init     .extend(c_emissions['global_init'])
    regional_constraints        .extend(c_emissions['regional'])
    regional_constraints_init   .extend(c_emissions['regional_init'])


    # Damage costs
    if damage_module == 'RICE2010':
        c_damages = damages.AD_RICE2010.constraints(m)
    elif damage_module == 'RICE2012':
        c_damages = damages.AD_RICE2012.constraints(m)
    elif damage_module == 'WITCH':
        c_damages = damages.AD_WITCH.constraints(m)
    else:
        raise NotImplementedError

    global_constraints          .extend(c_damages['global'])
    global_constraints_init     .extend(c_damages['global_init'])
    regional_constraints        .extend(c_damages['regional'])
    regional_constraints_init   .extend(c_damages['regional_init'])


    # Abatement costs
    c_abatement = abatement.constraints(m)

    global_constraints          .extend(c_abatement['global'])
    global_constraints_init     .extend(c_abatement['global_init'])
    regional_constraints        .extend(c_abatement['regional'])
    regional_constraints_init   .extend(c_abatement['regional_init'])


    # Cobb-Douglas and economics
    c_cobbdouglas = cobbdouglas.constraints(m)

    global_constraints          .extend(c_cobbdouglas['global'])
    global_constraints_init     .extend(c_cobbdouglas['global_init'])
    regional_constraints        .extend(c_cobbdouglas['regional'])
    regional_constraints_init   .extend(c_cobbdouglas['regional_init'])




    ######################
    # Optimisation
    ######################

    m.NPV = Var(m.t)
    m.PRTP = Param()
    global_constraints.append(lambda m,t: m.NPV[t] == m.NPV[t-1] + m.dt * exp(-m.PRTP * (m.year[t] - m.beginyear)) * sum(m.L(m.year(t),r) * m.utility[t,r] for r in m.regions) if t > 0 else Constraint.Skip)
    global_constraints_init.append(lambda m: m.NPV[0] == 0)

    
        
    for fct in global_constraints:
        name, fct = name_and_fct(fct)
        fullname = utils.add_constraint(m, Constraint(m.t, rule=fct), name)
    for fct in global_constraints_init:
        name, fct = name_and_fct(fct)
        fullname = utils.add_constraint(m, Constraint(rule=fct), name)
    for fct in regional_constraints:
        name, fct = name_and_fct(fct)
        fullname = utils.add_constraint(m, Constraint(m.t, m.regions, rule=fct), name)
    for fct in regional_constraints_init:
        name, fct = name_and_fct(fct)
        fullname = utils.add_constraint(m, Constraint(m.regions, rule=fct), name)

    m.obj = Objective(rule=lambda m: m.NPV[m.tf], sense=maximize)

    return m

def name_and_fct(fct):
    if isinstance(fct, tuple):
        name = fct[1]
        fct = fct[0]
    else:
        name = None
    return name, fct