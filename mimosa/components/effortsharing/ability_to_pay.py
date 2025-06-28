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

    TODO: description

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "ability_to_pay"
    model = MIMOSA(params)
    ```

    """

    m.effortsharing_AP_reductions_before_correction = Var(m.t, m.regions)
    m.effortsharing_AP_inv_correction_factor = Var(m.t)
    m.effortsharing_AP_allowances = Var(m.t, m.regions)

    def ability_to_pay_rule(m, t, r):
        gdp_var = m.baseline_GDP  # or: m.GDP_net
        per_cap_gdp = gdp_var[t, r] / m.population[t, r]
        global_per_cap_gdp = (
            sum(gdp_var[t, s] for s in m.regions) / m.global_population[t]
        )
        global_baseline_emissions = sum(m.baseline[t, s] for s in m.regions)

        reductions_before_correction = (
            (per_cap_gdp / global_per_cap_gdp) ** (1 / 3)
            * (global_baseline_emissions - m.global_emissions[t])
            / global_baseline_emissions
            * m.baseline[t, r]
        )

        return reductions_before_correction

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
