##############################################
# Model equations and constraints:
# Damage and adaptation costs, RICE specification
#
##############################################

import numpy as np
from model.common.pyomo import *

def constraints(m):
    """Damage and adaptation costs equations and constraints
    (RICE specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs multiplied by gross GDP)

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
    m.gross_damages = Var(m.t, m.regions)
    m.resid_damages = Var(m.t, m.regions)



    m.damage_a1 = Param(m.regions)
    m.damage_a2 = Param(m.regions)
    m.damage_a3 = Param(m.regions)
    m.damage_scale_factor = Param()

    m.adapt_level   = Var(m.t, m.regions, within=NonNegativeReals)
    m.adapt_costs   = Var(m.t, m.regions)
    m.adapt_FAD     = Var(m.t, m.regions, bounds=(0, 0.05))
    m.adapt_IAD     = Var(m.t, m.regions, bounds=(0, 0.15))
    m.adap1     = Param(m.regions)
    m.adap2     = Param(m.regions)
    m.adap3     = Param(m.regions)
    m.adapt_rho     = Param()
    m.fixed_adaptation = Param()

    m.adapt_SAD     = Var(m.t, m.regions, initialize=0.01, within=NonNegativeReals)


    # Sea level rise
    m.S1 = Param()
    m.S2 = Param()
    m.S3 = Param()
    m.SLR = Var(m.t)

    m.M1 = Param()
    m.M2 = Param()
    m.M3 = Param()
    m.M4 = Param()
    m.M5 = Param()
    m.M6 = Param()
    m.CUMGSIC = Var(m.t)
    m.CUMGIS = Var(m.t)

    m.SLRdam1 = Param(m.regions)
    m.SLRdam2 = Param(m.regions)
    m.total_SLR = Var(m.t)
    m.SLR_damages = Var(m.t, m.regions)

    global_constraints.extend([
        # Thermal expansion
        lambda m,t: m.SLR[t] == (1-m.S3)**(m.dt/10) * m.SLR[t-1] + m.S3 * (m.dt/10) * (m.temperature[t] * m.S1) if t > 0 else Constraint.Skip,

        # GSIC
        lambda m,t: m.CUMGSIC[t] == m.CUMGSIC[t-1] + m.M1 / m.M2 * m.dt * (m.M2 - m.CUMGSIC[t-1]) * (m.temperature[t-1] - m.M3) if t > 0 else Constraint.Skip,

        # GIS
        lambda m,t: m.CUMGIS[t] == m.CUMGIS[t-1] + (m.dt/10) * (1/100) * (m.M4 * m.temperature[t-1] + m.M5) * (1 - m.CUMGIS[t-1]/m.M6) if t > 0 else Constraint.Skip,

        lambda m,t: m.total_SLR[t] == m.SLR[t] + m.CUMGSIC[t] + m.CUMGIS[t],
    ])
    global_constraints_init.extend([
        lambda m: m.SLR[0] == m.S2 + m.S3 * (m.T0 * m.S1 - m.S2),
        lambda m: m.CUMGSIC[0] == 0.015,
        lambda m: m.CUMGIS[0] == 0.006
    ])
    regional_constraints.append(
        lambda m,t,r: m.SLR_damages[t,r] == 4 * (m.SLRdam1[r] * m.total_SLR[t] + m.SLRdam2[r] * m.total_SLR[t]**2) * (m.GDP_gross[t,r] / m.GDP_gross[0,r])**0.25
    )

    # Gross damages
    regional_constraints.extend([
        lambda m,t,r: m.gross_damages[t,r] == m.damage_scale_factor * damage_fct(m.temperature[t], m.T0, m, r),
        lambda m,t,r: m.resid_damages[t,r] == m.gross_damages[t,r] / (1 + m.adapt_level[t,r]) + m.SLR_damages[t,r],
        
        lambda m,t,r: m.adapt_level[t,r] == m.adap1[r] * (
            m.adap2[r] * (m.adapt_FAD[t,r]**2) ** (m.adapt_rho/2)
            +
            (1-m.adap2[r]) * (m.adapt_SAD[t,r]**2) ** (m.adapt_rho/2) # Because of positive bounds, this is valid
        ) ** (m.adap3[r] / m.adapt_rho),
        #lambda m,t,r: m.adapt_FAD[t,r] == 0.0001,
        lambda m,t,r: m.adapt_SAD[t,r] == (1-m.dk)**m.dt * m.adapt_SAD[t-1,r] + m.adapt_IAD[t,r] if t > 0 else Constraint.Skip,
        lambda m,t,r: m.adapt_costs[t,r] == m.adapt_FAD[t,r] + m.adapt_IAD[t,r],

        lambda m,t,r: m.damage_costs[t,r] == m.resid_damages[t,r] + m.adapt_costs[t,r],
    ])

    # Adaptation costs and residual damages
    # regional_constraints.extend([
        # lambda m,t,r: m.resid_damages[t,r]  == m.gross_damages[t,r] ,#/ (1 + m.adapt_level[t,r]),

        # lambda m,t,r: m.adapt_level[t,r] == m.adap1[r] * (
        #     ( m.adap2[r]    * m.adapt_FAD[t,r]**m.adapt_rho)
        #     +
        #     ((1-m.adap2[r]) * m.adapt_SAD[t,r]**m.adapt_rho)
        # ) ** (m.adap3[r] / m.adapt_rho),

        # lambda m,t,r: m.adapt_level[t,r] == m.adap1[r] * (
        #     ( m.adap2[r]    * m.adapt_FAD[t,r])
            
        # ) ** (m.adap3[r]),

        # lambda m,t,r: m.adapt_level[t,r]    == m.adap1[r] * (
        #     m.adap2[r]     * sqrt(m.adapt_FAD[t,r]) +
        #     (1-m.adap2[r]) * sqrt(m.adapt_SAD[t,r])
        # )** (2 * m.adap3[r]),

        # NOTE: Not sure if " * m.dt" should be here
        #lambda m,t,r: m.adapt_costs[t,r]  == (m.adapt_FAD[t,r]),# + m.adapt_IAD[t,r]),
        #lambda m,t,r: m.adapt_SADdot[t,r] == np.log(1-m.dk) * m.adapt_SAD[t,r] + m.adapt_IAD[t,r], 
    # ])

    # regional_constraints.extend([
    #     lambda m,t,r: m.damage_costs[t,r] == m.resid_damages[t,r] * m.GDP_gross[t,r]# + m.adapt_costs[t,r]
    # ])

    regional_constraints_init.extend([
        lambda m,r: m.adapt_FAD[0,r] == 0,
        lambda m,r: m.adapt_SAD[0,r] == 0,
        lambda m,r: m.adapt_IAD[0,r] == 0,
    #     # lambda m,r: m.gross_damages[0,r] == 0
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


# Adaptation cost function

def adaptation_costs(P, m, r):
    return _adaptation_costs(P, m.adapt_g1[r], m.adapt_g2[r])


def _adaptation_costs(P, gamma1, gamma2):
    return gamma1 * P**gamma2