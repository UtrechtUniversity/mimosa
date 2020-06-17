##############################################
# Model equations and constraints:
# Damage costs
#
##############################################

from pyomo.environ import *
from pyomo.dae import *

def constraints(m):
    regional_constraints = []
    global_constraints = []

    m.damage_costs  = Var(m.t, m.regions)
    m.smoothed_factor = Var(m.t)
    m.gross_damages = Var(m.t, m.regions)
    m.gross_damagesdot = DerivativeVar(m.gross_damages, wrt=m.t)
    m.resid_damages = Var(m.t, m.regions)
    m.adapt_costs   = Var(m.t, m.regions)
    m.adapt_level   = Var(m.t, m.regions, bounds=(0,1))

    m.damage_a1 = Param(m.regions)
    m.damage_a2 = Param(m.regions)
    m.damage_a3 = Param(m.regions)
    m.damage_scale_factor = Param()
    m.adapt_g1  = Param(m.regions)
    m.adapt_g2  = Param(m.regions)
    m.adapt_curr_level = Param()
    m.fixed_adaptation = Param()


    m.perc_reversible_damages = Param()

    global_constraints.append(
        lambda m,t: ((
            m.smoothed_factor[t] == (tanh((m.temperaturedot[t]) / 1e-3)+1)*(1-m.perc_reversible_damages)/2 +m.perc_reversible_damages
        ) if m.perc_reversible_damages < 1 else (m.smoothed_factor[t] == 1))
    )

    regional_constraints.append(
        lambda m,t,r: (
            m.gross_damagesdot[t,r] == m.damage_scale_factor * (
                damage_fct_dot(m.temperature, m, r)
                * m.smoothed_factor[t] * m.temperaturedot[t])
        ) if m.perc_reversible_damages < 1 else (
            m.gross_damages[t,r]  == m.damage_scale_factor * (
                damage_fct(m.temperature[t], m.T0, m, r))
        )
    )

    regional_constraints.extend([
        lambda m,t,r: m.adapt_level[t,r]    == m.adapt_curr_level if value(m.fixed_adaptation) else Constraint.Skip,
        lambda m,t,r: m.resid_damages[t,r]  == m.gross_damages[t,r] * (1-m.adapt_level[t,r]),
        lambda m,t,r: m.adapt_costs[t,r]    == adaptation_costs(m.adapt_level[t,r], m, r),
        lambda m,t,r: m.damage_costs[t,r]   == m.resid_damages[t,r] + m.adapt_costs[t,r]
    ])

    return regional_constraints, global_constraints




#################
## Utils
#################


def damage_fct(T, T0, m, r):
    return _damage_fct(T, m.damage_a1[r], m.damage_a2[r], m.damage_a3[r], T0)

def damage_fct_dot(T, m, r):
    return _damage_fct_dot(T, m.damage_a1[r], m.damage_a2[r], m.damage_a3[r])


def _damage_fct(T, a1, a2, a3, T0=None):
    """Quadratic damage function

    T: temperature
    T0 [None]: if specified, substracts damage at T0
    """
    fct = lambda temp: a1 * temp + a2 * temp**a3
    dmg = fct(T)
    if T0 is not None:
        dmg -= fct(T0)
    return dmg


def _damage_fct_dot(T, a1, a2, a3):
    return a1 + a2 * a3 * T ** (a3 - 1)



def adaptation_costs(P, m, r):
    return _adaptation_costs(P, m.adapt_g1[r], m.adapt_g2[r])

def _adaptation_costs(P, gamma1, gamma2):
    return gamma1 * P**gamma2