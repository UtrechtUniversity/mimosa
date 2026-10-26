"""
Model equations and constraints:
Damage and adaptation costs, COACCH specification
"""

from typing import Sequence
from mimosa.common import (
    ConcreteModel,
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
from mimosa.core.model_inputs import ModelInputs


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""
    The COACCH damage functions are split in two parts: temperature-dependent damages (non-SLR, as a function
    of global mean temperature above pre-industrial), and sea-level rise damages (SLR, as function of global mean
    sea-level rise in meters):

    With [combined damages](#param__economics.damages.coacch_combined_slr_nonslr_damages),
    the temperature-dependent curve includes SLR impacts and the separate SLR damage term is zero.

    $$
    \href{./#var__damage_costs}{\text{damages}_{t,r}} = \href{./#var__non_slr_damage_costs}{\text{damages}_{\text{non-SLR},t,r}} + \href{./#var__slr_damage_costs}{\text{damages}_{\text{SLR},t,r}}
    $$

    :::mimosa.components.damages.coacch.get_constraints_temperature_dependent

    :::mimosa.components.damages.coacch.get_constraints_slr



    ## Parameters defined in this module
    - param::damage_scale_factor
    - manualparam::damage quantile::economics.damages.quantile::


    """
    constraints = []
    m.damage_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
        doc="Total regional COACCH damage costs as a fraction of gross GDP, relative to the model start. Sum of the temperature-dependent and separate sea-level-rise damage terms.",
    )
    m.damage_costs_abs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        doc="Total regional COACCH damage costs in currency units, calculated as the damage fraction times gross GDP.",
    )
    m.damage_scale_factor = Param(
        initialize=inputs.config("economics.damages.scale factor")
    )
    m.non_market_damage_costs_abs = Param(
        m.t, m.regions, initialize=0.0, units=quant.unit("currency_unit")
    )
    m.global_damage_costs = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
        doc="Global COACCH damage costs as a fraction of global gross GDP, calculated from the sum of regional damage costs in currency units.",
    )
    m.adaptation_costs = Param(
        m.t, m.regions, units=quant.unit("fraction_of_GDP"), initialize=0.0
    )
    m.adaptation_costs_abs = Param(
        m.t, m.regions, units=quant.unit("currency_unit"), initialize=0.0
    )
    # Total damages are sum of non-SLR and SLR damages
    constraints.extend(
        [
            RegionalEquation(
                m.damage_costs,
                lambda m, t, r: m.non_slr_damage_costs[t, r] + m.slr_damage_costs[t, r],
            ),
            RegionalEquation(
                m.damage_costs_abs,
                lambda m, t, r: m.damage_costs[t, r] * m.GDP_gross[t, r],
            ),
            GlobalEquation(
                m.global_damage_costs,
                lambda m, t: (
                    sum(m.damage_costs_abs[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    # Get constraints for temperature dependent damages
    constraints.extend(get_constraints_temperature_dependent(m, inputs))

    # Get constraints for sea-level rise damages
    constraints.extend(get_constraints_slr(m, inputs))

    return constraints


def get_constraints_temperature_dependent(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""
    ## Temperature-dependent damages

    The temperature-dependent damages are modeled as a quadratic damage function $D(\cdot)$ of global mean temperature:

    $$
    D(x; \href{./#param__regional.COACCH.NoSLR_b1}{b_1}, \href{./#param__regional.COACCH.NoSLR_b2}{b_2}) = \href{./#param__regional.COACCH.NoSLR_b1}{b_1} \cdot x + \href{./#param__regional.COACCH.NoSLR_b2}{b_2} \cdot x^2.
    $$

    To calculate the damages, three transformations have to be taken from the above quadratic equation:

    * The COACCH damage functions were created as function of temperature relative to 1986-2005, which is 0.6°C above pre-industrial.
        For this reason, the temperature is shifted by 0.6°C.
    * The damages are scaled by a factor $a_{\href{./#param__economics.damages.quantile}{q},r}$, which depends on the quantile $\href{./#param__economics.damages.quantile}{q}$ of the damage function. This represents the uncertainty
        in the damage function. For median damages, this factor is $\href{./#param__regional.COACCH.NoSLR_a%20%28q%3D0.5%29}{a_{0.5,r}} = 1$. The quantile can be set using the [damage quantile parameter](#param__economics.damages.quantile).
    * Since we assume that until 2020 the climate damages are already incorporated in the baseline GDP,
        we subtract the damages of the initial time period $t=0$.

    Combining these three transformations, the damages are calculated as:

    $$
    \href{./#var__non_slr_damage_costs}{\text{damages}_{\text{non-SLR},t,r}} = a_{\href{./#param__economics.damages.quantile}{q},r} \cdot \big( D(\href{./#var__temperature}{\text{temperature}_t} - 0.6; \href{./#param__regional.COACCH.NoSLR_b1}{b_{1,r}}, \href{./#param__regional.COACCH.NoSLR_b2}{b_{2,r}}) -  D(\href{./#param__temperature.initial}{T_0} - 0.6; \href{./#param__regional.COACCH.NoSLR_b1}{b_{1,r}}, \href{./#param__regional.COACCH.NoSLR_b2}{b_{2,r}}) \big).
    $$

    The [regional functional form](#param__regional.COACCH.NoSLR_form) and the coefficients above describe
    the separate non-SLR curve. Combined curves use their own coefficients, selected by quantile and adaptation.

    All the damage coefficients are region-dependent (see [Damage functions and coefficients](coacch.md#damage-functions-and-coefficients)).

    ### Temperature-dependent damages aggregated to the world, and comparison with the literature:

    ``` plotly
    {"file_path": "./assets/plots/coacch_literature_comparison.json"}
    ```

    """
    constraints = []
    combined = inputs.config_value(
        "economics.damages.coacch_combined_slr_nonslr_damages"
    )
    quantile = inputs.config_value("economics.damages.quantile")
    adapt_prefix = (
        "Ad"
        if inputs.config_value("economics.damages.coacch_slr_withadapt")
        else "NoAd"
    )

    # Damages not related to SLR (dependent on temperature)
    m.non_slr_damage_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
        doc="Temperature-dependent regional damages as a fraction of gross GDP, relative to the model start. Includes sea-level-rise impacts when combined damage curves are selected.",
    )

    # Combined curves are quadratic and already incorporate the chosen quantile.
    m.damage_noslr_form = Param(
        m.regions,
        within=Any,
        initialize=(
            "Robust-Quadratic" if combined else inputs.regional("COACCH", "NoSLR_form")
        ),
    )  # String for functional form
    m.damage_noslr_b1 = Param(
        m.regions,
        initialize=inputs.regional(
            "COACCH",
            f"combined_b1_{adapt_prefix}-q{quantile}" if combined else "NoSLR_b1",
        ),
    )
    m.damage_noslr_b2 = Param(
        m.regions,
        initialize=inputs.regional(
            "COACCH",
            f"combined_b2_{adapt_prefix}-q{quantile}" if combined else "NoSLR_b2",
        ),
    )
    m.damage_noslr_b3 = Param(
        m.regions,
        within=Any,
        initialize=0 if combined else inputs.regional("COACCH", "NoSLR_b3"),
    )  # Can be empty
    # (b2 and b3 are only used for some functional forms)

    m.damage_noslr_a = Param(
        m.regions,
        initialize=(
            1 if combined else inputs.regional("COACCH", f"NoSLR_a (q={quantile})")
        ),
    )

    # Quadratic damage function for non-SLR damages. Factor `a` represents
    # the damage quantile
    constraints.append(
        RegionalEquation(
            m.non_slr_damage_costs,
            lambda m, t, r: (
                m.damage_scale_factor
                * damage_fct(m.temperature[t] - 0.6, m.T0 - 0.6, m, r, is_slr=False)
            ),
        )
    )

    return constraints


def get_constraints_slr(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""

    ## Sea-level rise damages

    In MIMOSA, sea-level rise damages are modelled separately from temperature dependent damages, as they occur
    on a different time scale: sea-level rise is a slow process with high inertia. Therefore, these damages are
    calculated as a function of global mean sea-level rise (SLR) in meters (calculated in the [Sea-level rise](../sealevelrise.md) component).

    The SLR damages are calculated with the DIVA impact model (see [Impact sectors used in the damage functions](coacch.md#impact-sectors-used-in-the-damage-functions)).
    These damages are available either with optimal adaptation (and include adaptation costs), or without adaptation. This can be
    chosen with the parameter [coacch_slr_withadapt](#param__economics.damages.coacch_slr_withadapt). By default, the optimal
    adaptation case is used.

    Depending on the region, the SLR damages are modelled with different functional forms following from a best-fit regression. The
    SLR damages are either quadratic, linear, or logistic:

    $$
    D_{\href{./#param__regional.COACCH.SLR-Ad_form}{\text{\{form\}}_r}}(\text{SLR}; \cdot) = \begin{cases}
    D_{\text{quadratic}}(\text{SLR}; \href{./#param__regional.COACCH.SLR-Ad_b1}{b_1}, \href{./#param__regional.COACCH.SLR-Ad_b2}{b_2}) = \href{./#param__regional.COACCH.SLR-Ad_b1}{b_1} \cdot \text{SLR} + \href{./#param__regional.COACCH.SLR-Ad_b2}{b_2} \cdot \text{SLR}^2\\[.2cm]
    D_{\text{linear}}(\text{SLR}; \href{./#param__regional.COACCH.SLR-Ad_b1}{b_1}) = \href{./#param__regional.COACCH.SLR-Ad_b1}{b_1} \cdot \text{SLR}\\[.2cm]
    D_{\text{logistic}}(\text{SLR}; \href{./#param__regional.COACCH.SLR-Ad_b1}{b_1}, \href{./#param__regional.COACCH.SLR-Ad_b2}{b_2}, \href{./#param__regional.COACCH.SLR-Ad_b3}{b_3}) = \frac{\href{./#param__regional.COACCH.SLR-Ad_b1}{b_1}}{1 + \href{./#param__regional.COACCH.SLR-Ad_b2}{b_2} \cdot e^{-\href{./#param__regional.COACCH.SLR-Ad_b3}{b_3} \cdot \text{SLR}}} - \frac{\href{./#param__regional.COACCH.SLR-Ad_b1}{b_1}}{1 + \href{./#param__regional.COACCH.SLR-Ad_b2}{b_2}}
    \end{cases}
    $$

    The values of $\href{./#param__regional.COACCH.SLR-Ad_b1}{b_1}$, $\href{./#param__regional.COACCH.SLR-Ad_b2}{b_2}$, and $\href{./#param__regional.COACCH.SLR-Ad_b3}{b_3}$ are region-dependent and depend on whether adaptation is included or not. These are different
    values than the coefficients in the temperature-dependent damages. The functional forms
    depend on the regression of the underlying impact data (see [Damage functions and coefficients](coacch.md#damage-functions-and-coefficients))
    and are shown in the table below.

    The coefficient links in the equations show the default, optimal-adaptation curve.
    Without adaptation, the corresponding regional inputs are the
    [functional form](#param__regional.COACCH.SLR-NoAd_form),
    [$b_1$](#param__regional.COACCH.SLR-NoAd_b1),
    [$b_2$](#param__regional.COACCH.SLR-NoAd_b2),
    [$b_3$](#param__regional.COACCH.SLR-NoAd_b3) and
    [median scale factor](#param__regional.COACCH.SLR-NoAd_a%20%28q%3D0.5%29).

    <div class="tiny_table table_first_col_header table_scrollable" markdown>
    {{ read_csv("docs/assets/data/coacch_slr_form.csv") }}
    </div>

    To calculate the SLR damage costs, two additional transformations have to be taken:

    * Similar to temperature-dependent damages, the SLR damages are scaled by a factor $a_{\href{./#param__economics.damages.quantile}{q},r}$, which depends on the quantile $\href{./#param__economics.damages.quantile}{q}$ of the damage function.
        This represents the uncertainty in the damage function. For median damages, this factor is $\href{./#param__regional.COACCH.SLR-Ad_a%20%28q%3D0.5%29}{a_{0.5,r}} = 1$. The quantile can be set using the
        [damage quantile parameter](#param__economics.damages.quantile).
    * Since we assume that until 2020 the climate damages are already incorporated in the baseline GDP,
        we subtract the damages of the initial time period $t=0$.

    The SLR damage costs therefore become:

    $$
    \href{./#var__slr_damage_costs}{\text{damages}_{\text{SLR},t,r}} = a_{\href{./#param__economics.damages.quantile}{q},r} \cdot \big( D_{\href{./#param__regional.COACCH.SLR-Ad_form}{\text{\{form\}}_r}}(\href{./#var__total_SLR}{\text{SLR}_t}; \cdot) - D_{\href{./#param__regional.COACCH.SLR-Ad_form}{\text{\{form\}}_r}}(\href{./#var__total_SLR}{\text{SLR}_0}; \cdot) \big).
    $$

    """
    constraints = []
    combined = inputs.config_value(
        "economics.damages.coacch_combined_slr_nonslr_damages"
    )
    quantile = inputs.config_value("economics.damages.quantile")
    adapt_prefix = (
        "Ad"
        if inputs.config_value("economics.damages.coacch_slr_withadapt")
        else "NoAd"
    )

    # SLR damages
    m.slr_damage_costs = Var(
        m.t,
        m.regions,
        bounds=(-0.5, 0.7),
        units=quant.unit("fraction_of_GDP"),
        doc="Regional sea-level-rise damages as a fraction of gross GDP, relative to initial sea level. Includes adaptation costs when optimal-adaptation curves are selected; zero when combined damage curves are used.",
    )

    # Combined curves already include SLR; keep the separate SLR parameters at zero.
    m.damage_slr_form = Param(
        m.regions,
        within=Any,
        initialize=(
            "Robust-Linear"
            if combined
            else inputs.regional("COACCH", f"SLR-{adapt_prefix}_form")
        ),
    )  # String for functional form
    m.damage_slr_b1 = Param(
        m.regions,
        initialize=(
            0 if combined else inputs.regional("COACCH", f"SLR-{adapt_prefix}_b1")
        ),
    )
    m.damage_slr_b2 = Param(
        m.regions,
        within=Any,
        initialize=(
            0 if combined else inputs.regional("COACCH", f"SLR-{adapt_prefix}_b2")
        ),
    )  # within=Any since it can be empty for some functional forms
    m.damage_slr_b3 = Param(
        m.regions,
        within=Any,
        initialize=(
            0 if combined else inputs.regional("COACCH", f"SLR-{adapt_prefix}_b3")
        ),
    )  # within=Any since it can be empty for some functional forms
    # (b2 and b3 are only used for some functional forms)

    m.damage_slr_a = Param(
        m.regions,
        initialize=(
            0
            if combined
            else inputs.regional("COACCH", f"SLR-{adapt_prefix}_a (q={quantile})")
        ),
    )

    # Linear damage function for SLR damages, including adaptation costs
    constraints.append(
        RegionalEquation(
            m.slr_damage_costs,
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
