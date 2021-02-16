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
        list of constraints (GlobalConstraint, GlobalInitConstraint, RegionalConstraint, RegionalInitConstraint)
    """
    constraints = []

    m.init_capitalstock_factor = Param(m.regions)
    m.capital_stock = Var(m.t, m.regions, initialize=lambda m,t,r: m.init_capitalstock_factor[r] * m.GDP(m.year(t), r))

    # Parameters
    m.alpha         = Param()
    m.dk            = Param()
    m.sr            = Param()
    m.elasmu        = Param()

    m.GDP_gross     = Var(m.t, m.regions, initialize=lambda m,t,r: m.GDP(m.year(0), r))
    m.GDP_net       = Var(m.t, m.regions)
    m.investments   = Var(m.t, m.regions)
    m.consumption   = Var(m.t, m.regions)
    m.utility       = Var(m.t, m.regions)

    m.ignore_damages = Param()

    # Cobb-Douglas, GDP, investments, capital, consumption and utility
    constraints.extend([
        RegionalConstraint(lambda m,t,r: m.GDP_gross[t,r] == economics.calc_GDP(
            m.TFP(m.year(t),r), 
            m.L(m.year(t),r),
            soft_min(m.capital_stock[t,r], scale=10),
            m.alpha
        ), 'GDP_gross'),
        RegionalConstraint(lambda m,t,r: m.GDP_net[t,r] == m.GDP_gross[t,r] * (1 - (m.damage_costs[t,r] if not value(m.ignore_damages) else 0)) - m.abatement_costs[t,r], 'GDP_net'),
        RegionalConstraint(lambda m,t,r: m.investments[t,r] == m.sr * m.GDP_net[t,r], 'investments'),
        RegionalConstraint(lambda m,t,r: m.consumption[t,r] == (1-m.sr) * m.GDP_net[t,r], 'consumption'),
        RegionalConstraint(lambda m,t,r: m.utility[t,r] == ( soft_min(m.consumption[t,r] / m.L(m.year(t),r)) ** (1-m.elasmu) - 1 ) / (1-m.elasmu) - 1, 'utility'),
        RegionalConstraint(lambda m,t,r: (
            m.capital_stock[t,r] == m.capital_stock[t-1,r] + m.dt * economics.calc_dKdt(m.capital_stock[t,r], m.dk, m.investments[t,r], m.dt)
        ) if t > 0 else Constraint.Skip, 'capital_stock'),
        RegionalInitConstraint(lambda m,r: m.capital_stock[0,r] == m.init_capitalstock_factor[r] * m.GDP(m.year(0), r))
    ])

    return constraints