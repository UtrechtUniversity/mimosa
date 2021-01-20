##############################################
# Model equations and constraints:
# Abatement costs
#
##############################################

from model.common.pyomo import *

def constraints(m):
    """Abatement cost equations and constraints

    Necessary variables:
        m.abatement_costs

    Returns:
        dict: {
            global:         global_constraints,
            global_init:    global_constraints_init,
            regional:       regional_constraints,
            regional_init:  regional_constraints_init
        }
    """
    global_constraints      = []
    global_constraints_init = []
    regional_constraints    = []
    regional_constraints_init = []
    
    ### Technological learning
    m.LBD_rate      = Param()
    m.log_LBD_rate  = Param(initialize=log(m.LBD_rate) / log(2))
    m.LBD_scaling   = Param()
    m.LBD_factor    = Var(m.t)
    global_constraints.append(lambda m,t:
        m.LBD_factor[t] == ((sum(m.baseline_cumulative(t,r) for r in m.regions) - m.cumulative_emissions[t])/m.LBD_scaling+1.0)**m.log_LBD_rate)

    m.LOT_rate      = Param()
    m.LOT_factor    = Var(m.t)
    global_constraints.append(lambda m,t: m.LOT_factor[t] == 1 / (1+m.LOT_rate)**t)

    m.learning_factor = Var(m.t)
    global_constraints.append(lambda m,t: m.learning_factor[t] == (m.LBD_factor[t] * m.LOT_factor[t]))

    m.abatement_costs = Var(m.t, m.regions)
    m.rel_abatement_costs = Var(m.t, m.regions)
    m.carbonprice = Var(m.t, m.regions)
    m.MAC_gamma     = Param()
    m.MAC_beta      = Param()

    regional_constraints.extend([
        lambda m,t,r: m.abatement_costs[t,r] == AC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta) * m.baseline[t,r],
        lambda m,t,r: m.rel_abatement_costs[t,r] == m.abatement_costs[t,r] / m.GDP_gross[t,r],
        lambda m,t,r: m.carbonprice[t,r] == MAC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta)
    ])

    regional_constraints_init.append(
        lambda m,r: m.carbonprice[0,r] == 0
    )

    return {
        'global':       global_constraints,
        'global_init':  global_constraints_init,
        'regional':     regional_constraints,
        'regional_init': regional_constraints_init
    }




#################
## Utils
#################


def MAC(a, factor, gamma, beta):
    return gamma * factor * a**beta

def AC(a, factor, gamma, beta):
    return gamma * factor * a**(beta+1) / (beta+1)