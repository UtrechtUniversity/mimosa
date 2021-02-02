##############################################
# Model equations and constraints:
# Damage and adaptation costs, RICE specification
#
##############################################

from model.common.pyomo import *

def constraints(m):
    """Damage and adaptation costs equations and constraints
    (RICE specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs, as % of GDP)

    Returns:
        list of constraints (GlobalConstraint, GlobalInitConstraint, RegionalConstraint, RegionalInitConstraint)
    """
    constraints = []

    m.damage_costs  = Var(m.t, m.regions)
    m.smoothed_factor = Var(m.t, bounds=(0,1))
    m.gross_damages = Var(m.t, m.regions)
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

    constraints.extend([

        # Smoothing factor for partially reversible damages
        GlobalConstraint(
            lambda m,t: ((
                m.smoothed_factor[t] == (tanh(((m.temperature[t] - m.temperature[t-1]) / m.dt) / 1e-3)+1)*(1-m.perc_reversible_damages)/2 +m.perc_reversible_damages
            ) if m.perc_reversible_damages < 1 and t > 0 else (m.smoothed_factor[t] == 1)),
            name='smoothed_factor'
        ),

        # Gross damages
        RegionalConstraint(
            lambda m,t,r: (
                m.gross_damages[t,r] == m.gross_damages[t-1, r] + m.dt * m.damage_scale_factor * (
                    damage_fct_dot(m.temperature[t], m, r)
                    * m.smoothed_factor[t] * (m.temperature[t] - m.temperature[t-1]) / m.dt)
            ) if m.perc_reversible_damages < 1 and t > 0 else ( ### TODO the "and t > 0" might break things up here when perc_reversible < 1
                m.gross_damages[t,r]  == m.damage_scale_factor * (
                    damage_fct(m.temperature[t], m.T0, m, r))
            ),
            name='gross_damages'
        ),
        RegionalConstraint(lambda m,t,r: m.gross_damages[t,r] >= 0),
        RegionalInitConstraint(lambda m,r: m.gross_damages[0,r] == 0)

    ])


    # Adaptation
    constraints.extend([
        RegionalConstraint(
            lambda m,t,r: m.adapt_level[t,r] == (
                m.adapt_curr_level
                if value(m.fixed_adaptation) else 
                (
                    optimal_adapt_level(m.gross_damages[t,r], m, r)
                    if value(m.adapt_g1[r]) * value(m.adapt_g2[r]) > 0 else
                    0
                )
            ),
            name='adapt_level'
        ),
        RegionalConstraint(lambda m,t,r: m.resid_damages[t,r]  == m.gross_damages[t,r] * (1-m.adapt_level[t,r]), 'resid_damages'),
        RegionalConstraint(lambda m,t,r: m.adapt_costs[t,r]    == adaptation_costs(m.adapt_level[t,r], m, r), 'adapt_costs'),
        RegionalConstraint(lambda m,t,r: m.damage_costs[t,r]   == m.resid_damages[t,r] + m.adapt_costs[t,r], 'damage_costs')
    ])

    return constraints




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
    fct = lambda temp: a1 * temp + a2 * pow(temp, a3, abs=True)
    dmg = fct(T)
    if T0 is not None:
        dmg -= fct(T0)
    return dmg


def _damage_fct_dot(T, a1, a2, a3):
    return a1 + a2 * a3 * T ** (a3 - 1)


# Adaptation cost function

def adaptation_costs(P, m, r):
    return _adaptation_costs(P, m.adapt_g1[r], m.adapt_g2[r])

def optimal_adapt_level(GD, m, r):
    eps = 0.0005
    return pow(GD / (m.adapt_g1[r] * m.adapt_g2[r]) + eps, 1/(m.adapt_g2[r]-1), abs=True)


def _adaptation_costs(P, gamma1, gamma2):
    # return gamma1 * pow(soft_relu(P, a=15), gamma2, abs=False)
    return gamma1 * pow(P, gamma2, abs=False)