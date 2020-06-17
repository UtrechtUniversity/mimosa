##############################################
# Model equations and constraints:
# Economics and Cobb-Douglas
#
##############################################

from pyomo.environ import *
from pyomo.dae import *
from model.common import economics

def constraints(m):
    """Economics and Cobb-Douglas equations and constraints

    Necessary variables:
        m.utility

    Returns:
        list: regional_constraints
        list: global_constraints
    """
    regional_constraints = []
    global_constraints = []

    m.init_capitalstock = Param(m.regions)
    m.capital_stock = Var(m.t, m.regions, initialize=lambda m,t,r: m.init_capitalstock[r])
    m.capital_stockdot          = DerivativeVar(m.capital_stock, wrt=m.t)

    # Parameters
    m.alpha         = Param()
    m.dk            = Param()
    m.sr            = Param()
    m.elasmu        = Param()

    m.GDP_gross     = Var(m.t, m.regions, initialize=lambda m: m.GDP(0, m.regions.first()))
    m.GDP_net       = Var(m.t, m.regions)
    m.investments   = Var(m.t, m.regions)
    m.consumption   = Var(m.t, m.regions, initialize=lambda m: (1-m.sr)*m.GDP(0, m.regions.first()))
    m.utility       = Var(m.t, m.regions)
    m.L = lambda t,r: m.population(t, r)

    m.dt = Param()

    regional_constraints.extend([
        lambda m,t,r: m.GDP_gross[t,r] == economics.calc_GDP(m.TFP(t, r), m.L(t,r), m.capital_stock[t,r], m.alpha),
        lambda m,t,r: m.GDP_net[t,r] == m.GDP_gross[t,r] * (1-m.damage_costs[t,r]) - m.abatement_costs[t,r],
        lambda m,t,r: m.investments[t,r] == m.sr * m.GDP_net[t,r],
        lambda m,t,r: m.consumption[t,r] == (1-m.sr) * m.GDP_net[t,r],
        lambda m,t,r: m.utility[t,r] == ( (m.consumption[t,r] / m.L(t,r)) ** (1-m.elasmu) - 1 ) / (1-m.elasmu) - 1,
        lambda m,t,r: m.capital_stockdot[t,r] == economics.calc_dKdt(m.capital_stock[t,r], m.dk, m.investments[t,r], m.dt)
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

    return regional_constraints, global_constraints