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
    RegionalEquation,
    GlobalEquation,
    value,
    soft_max,
    Any,
    exp,
    quant,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    The COACCH damage functions are split in two parts: temperature-dependent damages (non-SLR, as a function
    of global mean temperature above pre-industrial), and sea-level rise damages (SLR, as function of global mean
    sea-level rise in meters):

    $$
    \\text{damages}_{t,r} = \\text{damages}_{\\text{non-SLR},t,r} + \\text{damages}_{\\text{SLR},t,r}
    $$

    :::mimosa.components.damages.coacch._get_constraints_temperature_dependent

    :::mimosa.components.damages.coacch._get_constraints_slr



    ## Parameters defined in this module
    - param::damage_scale_factor
    - manualparam::damage quantile::economics.damages.quantile


    """
    constraints = []

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_scale_factor = Param(doc="::economics.damages.scale factor")
    m.damage_relative_global = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
    )
    # Total damages are sum of non-SLR and SLR damages
    constraints.extend(
        [
            RegionalEquation(
                m.damage_costs,
                lambda m, t, r: m.damage_costs_non_slr[t, r] + m.damage_costs_slr[t, r],
            ),
            GlobalEquation(
                m.damage_relative_global,
                lambda m, t: (
                    sum(m.damage_costs[t, r] * m.GDP_gross[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    # Get constraints for temperature dependent damages
    constraints.extend(_get_constraints_temperature_dependent(m))

    # Get constraints for sea-level rise damages
    constraints.extend(_get_constraints_slr(m))

    return constraints


def _get_constraints_temperature_dependent(
    m: AbstractModel,
) -> Sequence[GeneralConstraint]:
    """
    ## Temperature-dependent damages

    The temperature-dependent damages are modeled as a quadratic damage function $D(\\cdot)$ of global mean temperature:

    $$
    D(x; b_1, b_2) = b_1 \\cdot x + b_2 \\cdot x^2.
    $$

    To calculate the damages, three transformations have to be taken from the above quadratic equation:

    * The COACCH damage functions were created as function of temperature relative to 1986-2005, which is 0.6°C above pre-industrial.
        For this reason, the temperature is shifted by 0.6°C.
    * The damages are scaled by a factor $a_{q,r}$, which depends on the quantile $q$ of the damage function. This represents the uncertainty
        in the damage function. For median damages, this factor is $a_{0.5,r} = 1$. The quantile can be set using the [damage quantile parameter](../parameters.md#economics.damages.quantile).
    * Since we assume that until 2020 the climate damages are already incorporated in the baseline GDP,
        we subtract the damages of the initial time period $t=0$.

    Combining these three transformations, the damages are calculated as:

    $$
    \\text{damages}_{\\text{non-SLR},t,r} = a_{q,r} \\cdot \\big( D(\\text{temperature}_t - 0.6; b_{1,r}, b_{2,r}) -  D(T_0 - 0.6; b_{1,r}, b_{2,r}) \\big).
    $$

    All the damage coefficients are region-dependent (see [Damage functions and coefficients](./#damage-functions-and-coefficients)).

    ### Temperature-dependent damages aggregated to the world, and comparison with the literature:

    ``` plotly
    {"file_path": "./assets/plots/coacch_literature_comparison.json"}
    ```

    """
    constraints = []

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
        RegionalEquation(
            m.damage_costs_non_slr,
            lambda m, t, r: (
                m.damage_scale_factor
                * damage_fct(m.temperature[t] - 0.6, m.T0 - 0.6, m, r, is_slr=False)
            ),
        )
    )

    return constraints


def _get_constraints_slr(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    ## Sea-level rise damages

    In MIMOSA, sea-level rise damages are modelled separately from temperature dependent damages, as they occur
    on a different time scale: sea-level rise is a slow process with high inertia. Therefore, these damages are
    calculated as a function of global mean sea-level rise (SLR) in meters (calculated in the [Sea-level rise](sealevelrise.md) component).

    The SLR damages are calculated with the DIVA impact model (see [Impact sectors used in the damage functions](./#impact-sectors-used-in-the-damage-functions)).
    These damages are available either with optimal adaptation (and include adaptation costs), or without adaptation. This can be
    chosen with the parameter [coacch_slr_withadapt](../parameters.md#economics.damages.coacch_slr_withadapt). By default, the optimal
    adaptation case is used.

    Depending on the region, the SLR damages are modelled with different functional forms following from a best-fit regression. The
    SLR damages are either quadratic, linear, or logistic:

    $$
    D_{\\text{\\{form\\}}_r}(\\text{SLR}; \\cdot) = \\begin{cases}
    D_{\\text{quadratic}}(\\text{SLR}; b_1, b_2) = b_1 \\cdot \\text{SLR} + b_2 \\cdot \\text{SLR}^2\\\\[.2cm]
    D_{\\text{linear}}(\\text{SLR}; b_1) = b_1 \\cdot \\text{SLR}\\\\[.2cm]
    D_{\\text{logistic}}(\\text{SLR}; b_1, b_2, b_3) = \\frac{b_1}{1 + b_2 \\cdot e^{-b_3 \\cdot \\text{SLR}}} - \\frac{b_1}{1 + b_2}
    \\end{cases}
    $$

    The values of $b_1$, $b_2$, and $b_3$ are region-dependent and depend on whether adaptation is included or not. These are different
    values than the coefficients in the temperature-dependent damages. The functional form
    depends on the regression of the underlying impact data (see [Damage functions and coefficients](./#damage-functions-and-coefficients)),
    and are equal to:

    <div class="tiny_table table_first_col_header table_scrollable" markdown>
    {{ read_csv_macro("docs/assets/data/coacch_slr_form.csv") }}
    </div>

    To calculate the SLR damage costs, two additional transformations have to be taken:

    * Similar to temperature-dependent damages, the SLR damages are scaled by a factor $a_{q,r}$, which depends on the quantile $q$ of the damage function.
        This represents the uncertainty in the damage function. For median damages, this factor is $a_{0.5,r} = 1$. The quantile can be set using the
        [damage quantile parameter](../parameters.md#economics.damages.quantile).
    * Since we assume that until 2020 the climate damages are already incorporated in the baseline GDP,
        we subtract the damages of the initial time period $t=0$.

    The SLR damage costs therefore become:

    $$
    \\text{damages}_{\\text{SLR},t,r} = a_{q,r} \\cdot \\big( D_{\\text{\\{form\\}}_r}(\\text{SLR}_t; \\cdot) - D_{\\text{\\{form\\}}_r}(\\text{SLR}_0; \\cdot) \\big).
    $$

    """
    constraints = []

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
        RegionalEquation(
            m.damage_costs_slr,
            lambda m, t, r: (
                m.damage_scale_factor
                * damage_fct(m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True)
            ),
        )
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
