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
        list of constraints (GlobalConstraint, GlobalInitConstraint, RegionalConstraint, RegionalInitConstraint)
    """
    constraints = []
    
    ### Technological learning

    # Learning by doing
    m.LBD_rate      = Param()
    m.log_LBD_rate  = Param(initialize=log(m.LBD_rate) / log(2))
    m.LBD_scaling   = Param()
    m.LBD_factor    = Var(m.t)
    constraints.append(
        GlobalConstraint(
            lambda m,t: m.LBD_factor[t] == (sqrt(((sum(m.baseline_cumulative(m.year(0), m.year(t),r) for r in m.regions) - m.cumulative_emissions[t])/m.LBD_scaling)**2)+1.0)**m.log_LBD_rate,
            name='LBD'
        )
    )

    # Learning over time and total learning factor
    m.LOT_rate      = Param()
    m.LOT_factor    = Var(m.t)
    m.learning_factor = Var(m.t)
    constraints.extend([
        GlobalConstraint(lambda m,t: m.LOT_factor[t] == 1 / (1+m.LOT_rate)**t, 'LOT'),
        GlobalConstraint(lambda m,t: m.learning_factor[t] == (m.LBD_factor[t] * m.LOT_factor[t]), 'learning')
    ])

    # Abatement costs and MAC
    m.abatement_costs = Var(m.t, m.regions)
    m.rel_abatement_costs = Var(m.t, m.regions)
    m.carbonprice = Var(m.t, m.regions)
    m.MAC_gamma     = Param()
    m.MAC_beta      = Param()
    constraints.extend([
        RegionalConstraint(lambda m,t,r: m.abatement_costs[t,r] == AC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta) * m.baseline[t,r], 'abatement_costs'),
        RegionalConstraint(lambda m,t,r: m.rel_abatement_costs[t,r] == m.abatement_costs[t,r] / m.GDP_gross[t,r], 'rel_abatement_costs'),
        RegionalConstraint(lambda m,t,r: m.carbonprice[t,r] == MAC(m.relative_abatement[t,r], m.learning_factor[t], m.MAC_gamma, m.MAC_beta), 'carbonprice'),
        RegionalInitConstraint(lambda m,r: m.carbonprice[0,r] == 0)
    ])

    return constraints




#################
## Utils
#################


def MAC(a, factor, gamma, beta):
    return gamma * factor * a**beta

def AC(a, factor, gamma, beta):
    return gamma * factor * a**(beta+1) / (beta+1)

def soft_relu(x, a=10.0):
    return 1/a * log(1+exp(a*x))