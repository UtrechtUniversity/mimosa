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
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    soft_min,
    NonNegativeReals,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Damage and adaptation costs equations and constraints
    (RICE specification)

    Necessary variables:
        m.damage_costs (sum of residual damages and adaptation costs multiplied by gross GDP)

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
    m.gross_damages = Var(m.t, m.regions)
    m.resid_damages = Var(m.t, m.regions)

    m.damage_a1 = Param(m.regions, doc="regional::ADRICE2012.a1")
    m.damage_a2 = Param(m.regions, doc="regional::ADRICE2012.a2")
    m.damage_a3 = Param(m.regions, doc="regional::ADRICE2012.a3")
    m.damage_scale_factor = Param()

    m.adapt_level = Var(m.t, m.regions, within=NonNegativeReals)
    m.adapt_costs = Var(m.t, m.regions)
    m.adapt_FAD = Var(m.t, m.regions, bounds=(0, 0.15), initialize=0)
    m.adapt_IAD = Var(m.t, m.regions, bounds=(0, 0.15), initialize=0)
    m.adap1 = Param(m.regions, doc="regional::ADRICE2012.nu1")
    m.adap2 = Param(m.regions, doc="regional::ADRICE2012.nu2")
    m.adap3 = Param(m.regions, doc="regional::ADRICE2012.nu3")
    m.adapt_rho = Param(initialize=0.5)
    m.fixed_adaptation = Param()

    m.adapt_SAD = Var(m.t, m.regions, initialize=0.01, within=NonNegativeReals)

    # SLR damages
    m.SLRdam1 = Param(m.regions, doc="regional::ADRICE2012.slrdam1")
    m.SLRdam2 = Param(m.regions, doc="regional::ADRICE2012.slrdam2")
    m.SLR_damages = Var(m.t, m.regions)

    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.SLR_damages[t, r]
                == slr_damages(
                    m.total_SLR[t],
                    m.GDP_gross[t, r],
                    m.GDP_gross[0, r],
                    m.SLRdam1[r],
                    m.SLRdam2[r],
                ),
                "SLR_damages",
            ),
        ]
    )

    # Gross damages and adaptation levels
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.gross_damages[t, r]
                == m.damage_scale_factor * damage_fct(m.temperature[t], m.T0, m, r),
                "gross_damages",
            ),
            RegionalConstraint(
                lambda m, t, r: m.resid_damages[t, r]
                == m.gross_damages[t, r] / (1 + m.adapt_level[t, r])
                + m.SLR_damages[t, r],
                "resid_damages",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.adapt_SAD[t, r]
                    == (1 - m.dk) ** m.dt * m.adapt_SAD[t - 1, r] + m.adapt_IAD[t, r]
                    if t > 0
                    else Constraint.Skip
                ),
                "adapt_SAD",
            ),
            RegionalInitConstraint(lambda m, r: m.adapt_SAD[0, r] == 0),
            RegionalInitConstraint(lambda m, r: m.adapt_IAD[0, r] == 0),
            RegionalInitConstraint(lambda m, r: m.adapt_FAD[0, r] == 0),
            RegionalConstraint(
                lambda m, t, r: (
                    (
                        m.adapt_level[t, r]
                        == m.adap1[r]
                        * (
                            m.adap2[r]
                            * soft_min(m.adapt_FAD[t, r], scale=0.005) ** m.adapt_rho
                            + (1 - m.adap2[r])
                            * soft_min(m.adapt_SAD[t, r], scale=0.005) ** m.adapt_rho
                        )
                        ** (m.adap3[r] / m.adapt_rho)
                    )
                    if t > 0
                    else (m.adapt_level[t, r] == 0)
                ),
                name="adapt_level",
            ),
            RegionalConstraint(
                lambda m, t, r: m.adapt_costs[t, r]
                == m.adapt_FAD[t, r] + m.adapt_IAD[t, r],
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


def damage_fct(temperature, init_temp, m, r):
    power_fct = (
        lambda temp: m.damage_a1[r] * temp + m.damage_a2[r] * temp ** m.damage_a3[r]
    )

    damage = power_fct(soft_min(temperature))
    if init_temp is not None:
        damage -= power_fct(init_temp)

    return damage


# Sea level rise


def slr_damages(total_slr, gdp_t, gdp_0, dam1, dam2):
    return (
        4 * (dam1 * total_slr + dam2 * total_slr**2) * soft_min(gdp_t / gdp_0) ** 0.25
    )
