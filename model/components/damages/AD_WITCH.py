##############################################
# Model equations and constraints:
# Damage and adaptation costs, WITCH specification
#
##############################################

import numpy as np
from pyomo.environ import *
from pyomo.dae import *

def constraints(m):
    """Damage and adaptation costs equations and constraints
    (WITCH specification)

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

    # Gross and residual damages
    m.gross_damages = Var(m.t, m.regions)
    m.resid_damages = Var(m.t, m.regions)
    m.adapt_Q_ada   = Var(m.t, m.regions, initialize=0.1)

    m.damage_omega1_pos = Param(m.regions)
    m.damage_omega1_neg = Param(m.regions)
    m.damage_omega2_pos = Param(m.regions)
    m.damage_omega2_neg = Param(m.regions)
    m.damage_omega3_pos = Param(m.regions)
    m.damage_omega3_neg = Param(m.regions)
    m.damage_omega4_pos = Param(m.regions)
    m.damage_omega4_neg = Param(m.regions)

    m.adapt_eps     = Param(m.regions)

    m.damage_scale_factor = Param()

    regional_constraints.extend([
        lambda m,t,r: m.gross_damages[t,r] == m.damage_scale_factor * damage_fct(m.temperature[t], 0, m.T0, m, r),
        lambda m,t,r: m.resid_damages[t,r] == m.damage_scale_factor * damage_fct(m.temperature[t], m.adapt_Q_ada[t,r]**m.adapt_eps[r], m.T0, m, r)
    ])

    # Adaptation costs (protection costs, PC)
    m.adapt_costs             = Var(m.t, m.regions)
    m.adapt_costs_reactive    = Var(m.t, m.regions, bounds=(0,1)) # I_RADA
    # m.adapt_costs_proactive   = Var(m.t, m.regions, bounds=(0,1)) # I_PRADA
    # m.adapt_costs_speccap     = Var(m.t, m.regions) # I_SCAP, specific adaptive capacity
    m.fixed_adaptation = Param()

    regional_constraints.append(
        lambda m,t,r: m.adapt_costs[t,r] == (
            m.adapt_costs_reactive[t,r] # +
            # m.adapt_costs_proactive[t,r] +
            # m.adapt_costs_speccap[t,r]
        )
    )

    ## Nested Constant Elasticity of Substitution (CES)

    m.adapt_omega_eff_ada   = Param(m.regions)
    m.adapt_omega_act       = Param(m.regions)
    m.adapt_omega_eff_act   = Param(m.regions)
    m.adapt_omega_rada      = Param(m.regions)
    m.adapt_rho_ada         = Param(m.regions)
    m.adapt_rho_act         = Param(m.regions)

    # Nest 1: adaptation activities vs adaptive capacity
    # m.adapt_Q_act = Var(m.t, m.regions, initialize=0.1)
    m.adapt_Q_cap = Var(m.t, m.regions, initialize=0.1)

    regional_constraints.extend([
        lambda m,t,r: m.adapt_Q_ada[t,r] == m.adapt_omega_eff_ada[r] * m.adapt_omega_eff_act[r] * m.adapt_costs_reactive[t,r]
    ])

    # regional_constraints.append(lambda m,t,r: m.adapt_Q_ada[t,r] == CES(
    #     m.adapt_costs_reactive[t,r], m.adapt_Q_cap[t,r],
    #     # m.adapt_Q_act[t,r], m.adapt_Q_cap[t,r],
    #     m.adapt_omega_eff_ada[r], m.adapt_omega_act[r], m.adapt_rho_ada[r]
    # ))


    # Nest 2: reactive adaptation vs proactive adaptation
    # m.adapt_K_proactive = Var(m.t, m.regions, initialize=0.1)
    # regional_constraints.append(lambda m,t,r: m.adapt_Q_act[t,r] == CES(
    #     m.adapt_costs_reactive[t,r], m.adapt_K_proactive[t,r],
    #     m.adapt_omega_eff_act[r], m.adapt_omega_rada[r], m.adapt_rho_act[r]
    # ))

    # Nest 3: we don't model R&D and human capital, so we use the description
    # of Bosello et al (2010) [original AD-WITCH] that Q_cap is simple stock variable

    # Stocks of capital
    # m.adapt_Q_capdot        = DerivativeVar(m.adapt_Q_cap, wrt=m.t)
    # m.adapt_K_proactivedot  = DerivativeVar(m.adapt_K_proactive, wrt=m.t)

    # regional_constraints.extend([
    #     lambda m,t,r: m.adapt_Q_capdot[t,r]         == np.log(1-m.dk) * m.adapt_Q_cap[t,r] + m.adapt_costs_speccap[t,r],
    #     # lambda m,t,r: m.adapt_K_proactivedot[t,r]   == np.log(1-m.dk) * m.adapt_K_proactive[t,r] + m.adapt_costs_proactive[t,r],
    # ])

    
    regional_constraints.extend([
        lambda m,t,r: m.damage_costs[t,r] == m.resid_damages[t,r] + m.adapt_costs[t,r]
    ])

    regional_constraints_init.extend([
        # lambda m,r: m.adapt_K_proactive[0,r] == 0,
        lambda m,r: m.adapt_costs_reactive[0,r] == 0,
        # lambda m,r: m.adapt_costs[0,r] == 0
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

def damage_fct(T, Q_adapt, T0, m, r):
    return _damage_fct(
        T, Q_adapt, T0,
        m.damage_omega1_pos[r], m.damage_omega1_neg[r],
        m.damage_omega2_pos[r], m.damage_omega2_neg[r],
        m.damage_omega3_pos[r], m.damage_omega3_neg[r],
        m.damage_omega4_pos[r], m.damage_omega4_neg[r]
    )

def damage_fct_dot(T, Q_adapt, m, r):
    raise NotImplementedError


def _damage_fct(T, Q_adapt, T0, w1_pos, w1_neg, w2_pos, w2_neg, w3_pos, w3_neg, w4_pos, w4_neg):
    """Damage function

    T: temperature
    T0 [None]: if specified, substracts damage at T0
    """
    fct = lambda temp, adapt: (
        (w1_neg * temp + w2_neg * temp ** w3_neg + w4_neg) / (1+adapt) +
        (w1_pos * temp + w2_pos * temp ** w3_pos + w4_pos)
    )
    dmg = fct(T, Q_adapt)
    if T0 is not None:
        dmg -= fct(T0, 0)
    return dmg


# Constant Elasticity of Substitution
def CES(Q1, Q2, omega_eff, omega, rho):
    return omega_eff * (omega * Q1**rho + (1-omega) * Q2**rho) ** (1/rho)
