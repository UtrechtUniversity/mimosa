"""
Model equations and constraints:
Effort sharing
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    Constraint,
    RegionalConstraint,
    RegionalEquation,
    GlobalEquation,
    RegionalSoftEqualityConstraint,
    Any,
    quant,
    value,
    soft_min,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "ability_to_pay"
    model = MIMOSA(params)
    ```

    In this effort-sharing regime, emission allowances are allocated based on per-capita GDP (see [van den Berg et al. (2020)](https://doi.org/10.1007/s10584-019-02368-y)).

    There are three steps in the calculation of the allowances: (1) the main reduction calculation based on per-capita GDP,
    (2) a global correction factor to make sure that the total reductions match the global target, and (3) the final allowances calculation.


    :::mimosa.components.effortsharing.ability_to_pay.ability_to_pay_rule

    #### Step 2: Global correction factor

    The reduction factors from step 1 do not fully add up to the global emissions. There is typically a gap of a few percent. To correct this, a global correction factor is applied to the reductions:

    $$
    \\text{correction factor}_{t} = \\frac{\\text{global baseline emissions}_{t} - \\text{global emissions}_{t}}{\\sum_{r} \\text{reductions}_{\\text{AP}; t,r}}.
    $$

    #### Step 3: Final allowances calculation

    Finally, the allowances are calculated by subtracting the reductions from the baseline emissions, multiplied by the correction factor:

    $$
    \\text{allowances}_{\\text{AP}; t,r} = \\text{baseline emissions}_{t,r} - \\text{reductions}_{\text{AP}; t,r} \\cdot \\text{correction factor}_{t}.
    $$


    """

    m.effortsharing_AP_reductions_before_correction = Var(m.t, m.regions)
    m.effortsharing_AP_inv_correction_factor = Var(m.t)
    m.effortsharing_AP_allowances = Var(m.t, m.regions)

    return [
        RegionalEquation(
            m.effortsharing_AP_reductions_before_correction, ability_to_pay_rule
        ),
        GlobalEquation(
            m.effortsharing_AP_inv_correction_factor,
            lambda m, t: (
                (sum(m.baseline[t, r] for r in m.regions) - m.global_emissions[t])
                / soft_min(
                    sum(
                        m.effortsharing_AP_reductions_before_correction[t, r]
                        for r in m.regions
                    )
                )
                if t > 0
                else 1
            ),
        ),
        RegionalEquation(
            m.effortsharing_AP_allowances,
            lambda m, t, r: (
                m.baseline[t, r]
                - m.effortsharing_AP_reductions_before_correction[t, r]
                * m.effortsharing_AP_inv_correction_factor[t]
            ),
        ),
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.effortsharing_AP_allowances[t, r],
            lambda m, t, r: m.regional_emission_allowances[t, r],
            epsilon=None,
            absolute_epsilon=0.001,
            ignore_if=lambda m, t, r: t == 0,
            name="effortsharing_AP_rule",
        ),
    ]


def ability_to_pay_rule(m, t, r):
    """
    #### Step 1: Reductions before correction factor

    $$
    \\text{reductions}_{\\text{AP}; t,r} = \\sqrt[3]{\\frac{\\text{per cap. GDP}_{t,r}}{\\text{global per cap. GDP}_{t}}} \\cdot \\text{glob. fract. of baseline emissions}_{t} \\cdot \\text{baseline emissions}_{t,r},
    $$

    with

    $$
    \\text{glob. frac. of baseline emissions}_{t} = \\frac{\\text{global baseline emissions}_{t} - \\text{global emissions}_{t}}{\\text{global baseline emissions}_{t}}.
    $$

    *Note: The per-capita GDP can be calculated in two ways: either from the baseline GDP variable or from the net GDP variable. For numerical stability, we use the baseline GDP variable, even though it would be slightly more accurate to use the net GDP variable.*


    """
    gdp_var = m.baseline_GDP  # or: m.GDP_net
    per_cap_gdp = gdp_var[t, r] / m.population[t, r]
    global_per_cap_gdp = sum(gdp_var[t, s] for s in m.regions) / m.global_population[t]
    global_baseline_emissions = sum(m.baseline[t, s] for s in m.regions)

    reductions_before_correction = (
        (per_cap_gdp / global_per_cap_gdp) ** (1 / 3)
        * (global_baseline_emissions - m.global_emissions[t])
        / global_baseline_emissions
        * m.baseline[t, r]
    )

    return reductions_before_correction
