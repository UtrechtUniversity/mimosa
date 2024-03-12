"""
Model equations and constraints:
Damage and adaptation costs, RICE specification
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    soft_min,
    value,
    tanh,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Damage and adaptation costs equations and constraints
    (RICE specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs, as % of GDP)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.damage_costs = Var(m.t, m.regions)
    m.smoothed_factor = Var(m.t, bounds=(0, 1))
    m.gross_damages = Var(m.t, m.regions)
    m.resid_damages = Var(m.t, m.regions)
    m.adapt_costs = Var(m.t, m.regions)
    m.adapt_level = Var(m.t, m.regions, bounds=(0, 1))

    m.damage_a1 = Param(m.regions, doc="regional::ADRICE2010.a1")
    m.damage_a2 = Param(m.regions, doc="regional::ADRICE2010.a2")
    m.damage_a3 = Param(m.regions, doc="regional::ADRICE2010.a3")
    m.damage_scale_factor = Param()
    m.adapt_g1 = Param(m.regions, doc="regional::ADRICE2010.g1")
    m.adapt_g2 = Param(m.regions, doc="regional::ADRICE2010.g2")
    m.adapt_curr_level = Param()
    m.fixed_adaptation = Param()

    constraints.extend(
        [
            # Smoothing factor for partially reversible damages
            GlobalConstraint(
                lambda m, t: m.smoothed_factor[t]
                == smoothed_factor(t, m.temperature, m.dt, m.perc_reversible_damages),
                name="smoothed_factor",
            ),
            # Gross damages
            RegionalConstraint(
                lambda m, t, r: m.gross_damages[t, r]
                == calc_gross_damages(m, t, r, m.perc_reversible_damages),
                name="gross_damages",
            ),
            RegionalConstraint(lambda m, t, r: m.gross_damages[t, r] >= 0),
            RegionalInitConstraint(lambda m, r: m.gross_damages[0, r] == 0),
        ]
    )

    # Adaptation
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.adapt_level[t, r]
                == (
                    m.adapt_curr_level
                    if value(m.fixed_adaptation)
                    else optimal_adapt_level(m.gross_damages[t, r], m, r)
                ),
                name="adapt_level",
            ),
            RegionalConstraint(
                lambda m, t, r: m.resid_damages[t, r]
                == m.gross_damages[t, r] * (1 - m.adapt_level[t, r]),
                "resid_damages",
            ),
            RegionalConstraint(
                lambda m, t, r: m.adapt_costs[t, r]
                == adaptation_costs(m.adapt_level[t, r], m, r),
                "adapt_costs",
            ),
            RegionalConstraint(
                lambda m, t, r: m.damage_costs[t, r]
                == m.resid_damages[t, r] + m.adapt_costs[t, r],
                "damage_costs",
            ),
        ]
    )

    return constraints


#################
## Utils
#################


# Damage function


def calc_gross_damages(m, t, r, perc_reversible_damages):
    # If using partially irreversible damage, the damages
    # are calculated using a differential equation (delta_damage)
    if perc_reversible_damages < 1 and t > 0:
        delta_temperature = m.temperature[t] - m.temperature[t - 1]
        delta_damage = (
            damage_fct_dot(m.temperature[t], m, r)
            * m.smoothed_factor
            * delta_temperature
            / m.dt
        )
        return m.gross_damages[t - 1, r] + m.dt * m.damage_scale_factor * delta_damage

    # Otherwise, simply use the damage function
    return m.damage_scale_factor * damage_fct(m.temperature[t], m.T0, m, r)


def damage_fct(temperature, init_temp, m, r):
    power_fct = (
        lambda temp: m.damage_a1[r] * temp + m.damage_a2[r] * temp ** m.damage_a3[r]
    )

    damage = power_fct(soft_min(temperature))
    if init_temp is not None:
        damage -= power_fct(init_temp)

    return damage


def damage_fct_dot(temperature, m, r):
    """
    Derivative of the power function
    """
    return m.damage_a1[r] + m.damage_a2[r] * m.damage_a3[r] * temperature ** (
        m.damage_a3[r] - 1
    )


# Adaptation cost function
def adaptation_costs(adapt_level, m, r):
    return m.adapt_g1[r] * soft_min(adapt_level) ** m.adapt_g2[r]


def optimal_adapt_level(gross_damages, m, r):
    if value(m.adapt_g1[r]) * value(m.adapt_g2[r]) == 0:
        return 0

    eps = 0.0005
    return (soft_min(gross_damages, 0.01) / (m.adapt_g1[r] * m.adapt_g2[r]) + eps) ** (
        1 / (m.adapt_g2[r] - 1)
    )

    # return pow(GD / (m.adapt_g1[r] * m.adapt_g2[r]) + eps, 1/(m.adapt_g2[r]-1), abs=True)


# Partially irreversible damages:
def smoothed_factor(t, temperature, dt, perc_revers):
    if perc_revers < 1 and t > 0:
        delta_temp = temperature[t] - temperature[t - 1]
        return (tanh((delta_temp / dt) / 1e-3) + 1) * (
            1 - perc_revers
        ) / 2 + perc_revers

    return 1
