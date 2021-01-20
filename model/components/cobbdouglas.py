##############################################
# Model equations and constraints:
# Economics and Cobb-Douglas
#
##############################################

from model.common.pyomo import *
from model.common import economics

def constraints(m):
    """Economics and Cobb-Douglas equations and constraints

    Necessary variables:
        m.utility
        m.L (equal to m.population)
        m.dk

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

    m.init_capitalstock = Param(m.regions)
    m.capital_stock = Var(m.t, m.regions, initialize=lambda m,t,r: m.init_capitalstock[r])
    m.capital_stockdot          = DerivativeVar(m.capital_stock, wrt=m.t)

    # Parameters
    m.alpha         = Param()
    m.dk            = Param()
    m.sr            = Param()
    m.elasmu        = Param()

    m.GDP_gross     = Var(m.t, m.regions, initialize=lambda m: m.GDP[0, m.regions.first()])
    m.GDP_net       = Var(m.t, m.regions)
    m.investments   = Var(m.t, m.regions)
    m.consumption   = Var(m.t, m.regions, initialize=lambda m: (1-m.sr)*m.GDP[0, m.regions.first()])
    m.utility       = Var(m.t, m.regions)

    m.dt = Param()

    m.ignore_damages = Param()

    regional_constraints.extend([
        lambda m,t,r: m.GDP_gross[t,r] == economics.calc_GDP(m.TFP[t,r], m.L[t,r], m.capital_stock[t,r], m.alpha),
        lambda m,t,r: m.GDP_net[t,r] == m.GDP_gross[t,r] - (m.damage_costs[t,r] if not value(m.ignore_damages) else 0) - m.abatement_costs[t,r],
        lambda m,t,r: m.investments[t,r] == m.sr * m.GDP_net[t,r],
        lambda m,t,r: m.consumption[t,r] == (1-m.sr) * m.GDP_net[t,r],
        lambda m,t,r: m.utility[t,r] == ( (m.consumption[t,r] / m.L[t,r]) ** (1-m.elasmu) - 1 ) / (1-m.elasmu) - 1,
        lambda m,t,r: (
            m.capital_stockdot[t,r] == economics.calc_dKdt(m.capital_stock[t,r], m.dk, m.investments[t,r], m.dt)
        ) if t > 0 else Constraint.Skip
    ])

    m.consumption_NPV = Var(m.t)
    m.consumption_NPVdot = DerivativeVar(m.consumption_NPV, wrt=m.t)
    m.baseline_consumption_NPV = Var(m.t, initialize=0.01)
    m.baseline_consumption_NPVdot = DerivativeVar(m.baseline_consumption_NPV, wrt=m.t)
    m.consumption_loss = Var(m.t)
    global_constraints.extend([
        lambda m,t: m.consumption_NPVdot[t] == sum(exp(-0.05 * t) * m.consumption[t,r] for r in m.regions),
        lambda m,t: m.baseline_consumption_NPVdot[t] == sum(exp(-0.05 * t) * (1-m.sr) * m.GDP[t,r] for r in m.regions),
        lambda m,t: m.consumption_loss[t] == 1 - m.consumption_NPV[t] / m.baseline_consumption_NPV[t] if t > 0 else Constraint.Skip
    ])
    global_constraints_init.extend([
        lambda m: m.consumption_NPV[0] == 0,
        lambda m: m.baseline_consumption_NPV[0] == 0,
        lambda m: m.consumption_loss[0] == 0
    ])

    regional_constraints_init.append(
        lambda m,r: m.capital_stock[0,r] == m.init_capitalstock[r]
    )

    return {
        'global':       global_constraints,
        'global_init':  global_constraints_init,
        'regional':     regional_constraints,
        'regional_init': regional_constraints_init
    }