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
from model.components import emissions, abatement, cobbdouglas, damages


######################
# Create model
######################


def create_abstract_model(damage_module="RICE"):

    m = AbstractModel()

    ## Constraints
    # Each global / regional constraint will be put in these lists,
    # then added to the model at the end of this file.
    global_constraints = []
    global_constraints_init = []
    regional_constraints = []
    regional_constraints_init = []

    ## Time and region
    m.beginyear = Param()
    m.endyear = Param()
    m.tf = Param(initialize=m.endyear - m.beginyear)
    m.year2100 = Param(initialize=2100 - m.beginyear)
    m.t = ContinuousSet(bounds=(0, m.tf))

    m.regions = Set(ordered=True, dimen=1)

    ######################
    # Create data functions
    # Will be initialised when creating a concrete instance of the model
    ######################

    m.baseline_emissions = None
    m.population = None
    m.TFP = None
    m.GDP = None
    m.carbon_intensity = None

    def baseline_cumulative(t_end, region):
        t_values = np.linspace(0, t_end, 100)
        return np.trapz(m.baseline_emissions[t_values, region], x=t_values)

    m.baseline_cumulative = baseline_cumulative

    ######################
    # Components
    ######################

    # Emissions and temperature equations
    c_emissions = emissions.constraints(m)

    global_constraints.extend(c_emissions["global"])
    global_constraints_init.extend(c_emissions["global_init"])
    regional_constraints.extend(c_emissions["regional"])
    regional_constraints_init.extend(c_emissions["regional_init"])

    # Damage costs
    if damage_module == "RICE2010":
        c_damages = damages.AD_RICE2010.constraints(m)
    elif damage_module == "RICE2012":
        c_damages = damages.AD_RICE2012.constraints(m)
    elif damage_module == "WITCH":
        c_damages = damages.AD_WITCH.constraints(m)
    else:
        raise NotImplementedError

    global_constraints.extend(c_damages["global"])
    global_constraints_init.extend(c_damages["global_init"])
    regional_constraints.extend(c_damages["regional"])
    regional_constraints_init.extend(c_damages["regional_init"])

    # Abatement costs
    c_abatement = abatement.constraints(m)

    global_constraints.extend(c_abatement["global"])
    global_constraints_init.extend(c_abatement["global_init"])
    regional_constraints.extend(c_abatement["regional"])
    regional_constraints_init.extend(c_abatement["regional_init"])

    # Cobb-Douglas and economics
    c_cobbdouglas = cobbdouglas.constraints(m)

    global_constraints.extend(c_cobbdouglas["global"])
    global_constraints_init.extend(c_cobbdouglas["global_init"])
    regional_constraints.extend(c_cobbdouglas["regional"])
    regional_constraints_init.extend(c_cobbdouglas["regional_init"])

    ######################
    # Optimisation
    ######################

    m.NPV = Var(m.t)
    m.NPVdot = DerivativeVar(m.NPV, wrt=m.t)
    m.PRTP = Param()
    global_constraints.append(
        lambda m, t: m.NPVdot[t]
        == exp(-m.PRTP * t) * sum(m.L[t, r] * m.utility[t, r] for r in m.regions)
    )
    global_constraints_init.append(lambda m: m.NPV[0] == 0)

    for fct in global_constraints:
        utils.add_constraint(m, Constraint(m.t, rule=fct))
    for fct in global_constraints_init:
        utils.add_constraint(m, Constraint(rule=fct))
    for fct in regional_constraints:
        utils.add_constraint(m, Constraint(m.t, m.regions, rule=fct))
    for fct in regional_constraints_init:
        utils.add_constraint(m, Constraint(m.regions, rule=fct))

    m.obj = Objective(rule=lambda m: m.NPV[m.tf], sense=maximize)

    return m
