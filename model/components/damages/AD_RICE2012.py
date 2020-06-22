##############################################
# Model equations and constraints:
# Damage and adaptation costs, RICE specification
#
##############################################

import numpy as np
from pyomo.environ import *
from pyomo.dae import *

def constraints(m):
    """Damage and adaptation costs equations and constraints
    (RICE specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs, % of GDP)

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

    m.damage_costs  = Var(m.t, m.regions)
    m.smoothed_factor = Var(m.t)
    m.gross_damages = Var(m.t, m.regions)
    m.gross_damagesdot = DerivativeVar(m.gross_damages, wrt=m.t)
    m.resid_damages = Var(m.t, m.regions)



    m.damage_a1 = Param(m.regions)
    m.damage_a2 = Param(m.regions)
    m.damage_a3 = Param(m.regions)
    m.damage_scale_factor = Param()

    m.adapt_level   = Var(m.t, m.regions, within=NonNegativeReals)
    m.adapt_costs   = Var(m.t, m.regions)
    min_adapt_FAD   = 0.00001
    m.adapt_FAD     = Var(m.t, m.regions, bounds=(min_adapt_FAD, 0.2))
    m.adapt_IAD     = Var(m.t, m.regions, bounds=(min_adapt_FAD, 0.5))
    m.adapt_nu1     = Param(m.regions)
    m.adapt_nu2     = Param(m.regions)
    m.adapt_nu3     = Param(m.regions)
    m.adapt_rho     = Param()
    m.fixed_adaptation = Param()

    m.adapt_SAD     = Var(m.t, m.regions, initialize=0.0002)
    m.adapt_SADdot  = DerivativeVar(m.adapt_SAD, wrt=m.t)

    regional_constraints.extend([
        lambda m,t,r: m.resid_damages[t,r]  == m.gross_damages[t,r] / (1 + m.adapt_level[t,r]),
        lambda m,t,r: m.adapt_level[t,r]    == (
            m.adapt_nu1[r] * sqrt(m.adapt_SAD[t,r]) +
            m.adapt_nu2[r] * sqrt(m.adapt_FAD[t,r])
        )** (2 * m.adapt_nu3[r]),

        # NOTE: Not sure if " * m.dt" should be here
        lambda m,t,r: m.adapt_costs[t,r]  == (m.adapt_FAD[t,r] + m.adapt_IAD[t,r]) * m.dt,
        lambda m,t,r: m.adapt_SADdot[t,r] == np.log(1-m.dk) * m.adapt_SAD[t,r] + m.adapt_IAD[t,r], 
    ])

    regional_constraints.append(
        lambda m,t,r: (m.gross_damages[t,r]  == m.damage_scale_factor * (
                damage_fct(m.temperature[t], m.T0, m, r)
            )) if m.damage_scale_factor > 0 else (m.gross_damages[t,r] == 0)
    )

    regional_constraints.extend([
        lambda m,t,r: m.damage_costs[t,r]   == m.resid_damages[t,r] + m.adapt_costs[t,r]
    ])

    regional_constraints_init.extend([
        lambda m,r: m.adapt_IAD[0,r] == 0,
        lambda m,r: m.adapt_FAD[0,r] == min_adapt_FAD,
        lambda m,r: m.adapt_SAD[0,r] == min_adapt_FAD,
        # lambda m,r: m.gross_damages[0,r] == 0
    ])

    return {
        'global':       global_constraints,
        'global_init':  global_constraints_init,
        'regional':     regional_constraints,
        'regional_init': regional_constraints_init
    }




#################
## Utils
#################


# Damage function

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


# Adaptation cost function

def adaptation_costs(P, m, r):
    return _adaptation_costs(P, m.adapt_g1[r], m.adapt_g2[r])


def _adaptation_costs(P, gamma1, gamma2):
    return gamma1 * P**gamma2