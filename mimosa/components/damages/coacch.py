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
    value,
    soft_max,
    Any,
    exp,
    quant,
)


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

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_scale_factor = Param(doc="::economics.damages.scale factor")

    # Damages not related to SLR (dependent on temperature)
    m.damage_costs_non_slr = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))

    m.damage_noslr_form = Param(
        m.regions, within=Any, doc="regional::COACCH.NoSLR_form"
    )  # String for functional form
    m.damage_noslr_b1 = Param(m.regions, doc="regional::COACCH.NoSLR_b1")
    m.damage_noslr_b2 = Param(m.regions, doc="regional::COACCH.NoSLR_b2")
    m.damage_noslr_b3 = Param(
        m.regions, within=Any, doc="regional::COACCH.NoSLR_b3"
    )  # Can be empty
    # (b2 and b3 are only used for some functional forms)

    m.damage_noslr_a = Param(
        m.regions,
        doc=lambda params: f'regional::COACCH.NoSLR_a (q={params["economics"]["damages"]["quantile"]})',
    )

    # Quadratic damage function for non-SLR damages. Factor `a` represents
    # the damage quantile
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.damage_costs_non_slr[t, r]
            == m.damage_scale_factor
            * damage_fct(m.temperature[t] - 0.6, m.T0 - 0.6, m, r, is_slr=False),
            "damage_costs_non_slr",
        )
    )

    # SLR damages
    m.damage_costs_slr = Var(
        m.t, m.regions, bounds=(-0.5, 0.7), units=quant.unit("fraction_of_GDP")
    )

    def slr_param_name(params, name):
        """Returns the parameter name regional::COACCH.SLR... depending on if adaptation is included or not."""
        slr_with_adapt = params["economics"]["damages"]["coacch_slr_withadapt"]
        return f'regional::COACCH.SLR-{"Ad" if slr_with_adapt else "NoAd"}_{name}'

    m.damage_slr_form = Param(
        m.regions,
        within=Any,
        doc=lambda params: slr_param_name(params, "form"),
    )  # String for functional form
    m.damage_slr_b1 = Param(
        m.regions,
        doc=lambda params: slr_param_name(params, "b1"),
    )
    m.damage_slr_b2 = Param(
        m.regions,
        within=Any,
        doc=lambda params: slr_param_name(params, "b2"),
    )  # within=Any since it can be empty for some functional forms
    m.damage_slr_b3 = Param(
        m.regions,
        within=Any,
        doc=lambda params: slr_param_name(params, "b3"),
    )  # within=Any since it can be empty for some functional forms
    # (b2 and b3 are only used for some functional forms)

    m.damage_slr_a = Param(
        m.regions,
        doc=lambda params: slr_param_name(
            params, f'a (q={params["economics"]["damages"]["quantile"]})'
        ),
    )

    # Linear damage function for SLR damages, including adaptation costs
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.damage_costs_slr[t, r]
            == m.damage_scale_factor
            * damage_fct(m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True),
            "damage_costs_slr",
        )
    )

    # Total damages are sum of non-SLR and SLR damages
    constraints.append(
        RegionalConstraint(
            lambda m, t, r: m.damage_costs[t, r]
            == m.damage_costs_non_slr[t, r] + m.damage_costs_slr[t, r],
            "damage_costs",
        ),
    )

    return constraints


#################
## Utils
#################


# Damage function


def functional_form(x, m, r, is_slr=False):
    if is_slr:
        form = m.damage_slr_form[r]
        b1, b2, b3 = m.damage_slr_b1[r], m.damage_slr_b2[r], m.damage_slr_b3[r]
        a = m.damage_slr_a[r]
    else:
        form = m.damage_noslr_form[r]
        b1, b2, b3 = m.damage_noslr_b1[r], m.damage_noslr_b2[r], m.damage_noslr_b3[r]
        a = m.damage_noslr_a[r]

    # Linear functional form
    if "Linear" in value(form):
        return a * b1 * x / 100.0

    # Quadratic functional form
    if "Quadratic" in value(form):
        return a * (b1 * x + b2 * x**2) / 100.0

    # Logistic functional form
    if "Logistic" in value(form):
        return a * logistic(x, b1, b2, b3) / 100.0

    raise NotImplementedError


def damage_fct(x, x0, m, r, is_slr):
    damage = functional_form(x, m, r, is_slr)
    if x0 is not None:
        damage -= functional_form(x0, m, r, is_slr)

    return damage


def logistic(x, b1, b2, b3):
    exponent = soft_max(-b3 * x, 10, scale=0.1)  # Avoid exponential overflow
    return b1 / (1 + b2 * exp(exponent)) - b1 / (1 + b2)
