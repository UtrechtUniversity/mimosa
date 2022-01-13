"""
Model equations and constraints:
Damage and adaptation costs, RICE specification
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    Constraint,
    value,
    soft_max,
    soft_min,
    Any,
    exp,
)
from model.common.pyomo_utils import RegionalInitConstraint


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Damage and adaptation costs equations and constraints
    (COACCH specification)

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
    m.damage_scale_factor = Param()

    # Damages not related to SLR (dependent on temperature)
    m.gross_damages = Var(m.t, m.regions)
    m.resid_damages = Var(m.t, m.regions)

    m.damage_noslr_form = Param(m.regions, within=Any)  # String for functional form
    m.damage_noslr_b1 = Param(m.regions)
    m.damage_noslr_b2 = Param(m.regions)
    m.damage_noslr_b3 = Param(m.regions, within=Any)
    # (b2 and b3 are only used for some functional forms)

    m.damage_noslr_a = Param(m.regions)

    # Quadratic damage function for non-SLR damages. Factor `a` represents
    # the damage quantile
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.gross_damages[t, r]
            == m.damage_scale_factor
            * damage_fct(m.temperature[t] - 0.6, m.T0 - 0.6, m, r, is_slr=False),
            "gross_damages",
        )
    )

    # SLR damages
    m.SLR_damages = Var(m.t, m.regions, bounds=(-0.5, 0.7))

    m.SLR_damages_opt_adapt = Var(m.t, m.regions, bounds=(-0.5, 0.7))
    m.SLR_damages_no_adapt = Var(m.t, m.regions, bounds=(-0.5, 0.7))
    m.SLR_adapt_param = Param()
    m.SLR_adapt_level = Var(m.t, m.regions, bounds=(0, 1))

    ## SLR damages are calculated both for optimal adaptation and no adaptation
    m.damage_slr_form_opt_adapt = Param(
        m.regions, within=Any
    )  # String for functional form
    m.damage_slr_b1_opt_adapt = Param(m.regions)
    m.damage_slr_b2_opt_adapt = Param(m.regions, within=Any)
    m.damage_slr_b3_opt_adapt = Param(m.regions, within=Any)

    m.damage_slr_a_opt_adapt = Param(m.regions)

    m.damage_slr_form_no_adapt = Param(
        m.regions, within=Any
    )  # String for functional form
    m.damage_slr_b1_no_adapt = Param(m.regions)
    m.damage_slr_b2_no_adapt = Param(m.regions, within=Any)
    m.damage_slr_b3_no_adapt = Param(m.regions, within=Any)

    m.damage_slr_a_no_adapt = Param(m.regions)

    # Linear damage function for SLR damages, including adaptation costs
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.SLR_adapt_level[t, r] == m.SLR_adapt_param,
                "SLR_damages_adapt_level",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.SLR_damages[t, r]
                    if value(m.SLR_adapt_param) == 1
                    else m.SLR_damages_opt_adapt[t, r]
                )
                == m.damage_scale_factor
                * damage_fct(
                    m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True, slr_adapt=True
                ),
                "SLR_damages_opt_adapt",
            ),
            RegionalConstraint(
                lambda m, t, r: (
                    m.SLR_damages[t, r]
                    if value(m.SLR_adapt_param) == 0
                    and value(m.SLR_adapt_param) is not False
                    else m.SLR_damages_no_adapt[t, r]
                )
                == m.damage_scale_factor
                * damage_fct(
                    m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True, slr_adapt=False
                ),
                "SLR_damages_no_adapt",
            ),
            # Interpolate between optimal and no adaptation
            # (only when SLR_adapt_param > 0 and < 1):
            RegionalConstraint(
                lambda m, t, r: m.SLR_damages[t, r]
                == m.SLR_adapt_level[t, r] * m.SLR_damages_opt_adapt[t, r]
                + (1 - m.SLR_adapt_level[t, r]) * m.SLR_damages_no_adapt[t, r]
                if (value(m.SLR_adapt_param) > 0 and value(m.SLR_adapt_param) < 1)
                or value(m.SLR_adapt_param) is False
                else Constraint.Skip,
                "SLR_damages",
            ),
        ]
    )

    # Adaptation
    m.adapt_level = Var(m.t, m.regions, bounds=(0, 1), initialize=0.001)
    m.adapt_costs = Var(m.t, m.regions, initialize=0)
    m.adapt_costs_g1 = Param(m.regions)
    m.adapt_costs_g2 = Param(m.regions)
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.resid_damages[t, r]
                == m.gross_damages[t, r] * (1 - m.adapt_level[t, r]),
                "resid_damages",
            ),
            RegionalConstraint(
                lambda m, t, r: m.adapt_costs[t, r]
                == adaptation_costs(m.adapt_level[t, r], m, r),
                "adaptation_costs",
            ),
            RegionalInitConstraint(
                lambda m, r: m.adapt_level[0, r] == 0, "adaptation_level_init"
            ),
        ]
    )

    # Total damages are sum of non-SLR and SLR damages
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.damage_costs[t, r]
            == m.resid_damages[t, r] + m.SLR_damages[t, r] + m.adapt_costs[t, r],
            "damage_costs",
        ),
    )

    return constraints


#################
## Utils
#################


# Damage function


def functional_form(x, m, r, is_slr=False, slr_adapt=False):
    if is_slr and slr_adapt:
        form = m.damage_slr_form_opt_adapt[r]
        b1, b2, b3 = (
            m.damage_slr_b1_opt_adapt[r],
            m.damage_slr_b2_opt_adapt[r],
            m.damage_slr_b3_opt_adapt[r],
        )
        a = m.damage_slr_a_opt_adapt[r]
    elif is_slr and not slr_adapt:
        form = m.damage_slr_form_no_adapt[r]
        b1, b2, b3 = (
            m.damage_slr_b1_no_adapt[r],
            m.damage_slr_b2_no_adapt[r],
            m.damage_slr_b3_no_adapt[r],
        )
        a = m.damage_slr_a_no_adapt[r]
    else:
        form = m.damage_noslr_form[r]
        b1, b2, b3 = m.damage_noslr_b1[r], m.damage_noslr_b2[r], m.damage_noslr_b3[r]
        a = m.damage_noslr_a[r]

    # Linear functional form
    if "Linear" in value(form):
        return a * b1 * x / 100.0

    # Quadratic functional form
    if "Quadratic" in value(form):
        return a * (b1 * x + b2 * x ** 2) / 100.0

    # Logistic functional form
    if "Logistic" in value(form):
        return a * logistic(x, b1, b2, b3) / 100.0

    raise NotImplementedError


def damage_fct(x, x0, m, r, is_slr: bool, slr_adapt: bool = True):
    damage = functional_form(x, m, r, is_slr, slr_adapt)
    if x0 is not None:
        damage -= functional_form(x0, m, r, is_slr, slr_adapt)

    return damage


def logistic(x, b1, b2, b3):
    exponent = soft_max(-b3 * x, 10, scale=0.1)  # Avoid exponential overflow
    return b1 / (1 + b2 * exp(exponent)) - b1 / (1 + b2)


# Adaptation cost function


def adaptation_costs(adapt_level, m, r):
    return m.adapt_costs_g1[r] * soft_min(adapt_level) ** m.adapt_costs_g2[r]
