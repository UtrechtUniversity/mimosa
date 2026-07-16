"""
Model equations and constraints:
Utility and global welfare
"""

from typing import Sequence

from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    soft_min,
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    <h3>General inequality aversion</h3>

    This setting makes the weight given to inequality between regions explicit. Let $C_{t,r}$
    be regional consumption, $L_{t,r}$ population, $\\eta$ the inequality-aversion parameter
    (`inequal_aversion`), and $\\mu$ the elasticity of marginal utility (`elasmu`). MIMOSA first
    calculates:

    $$
    U_{t,r} = L_{t,r}
    \\left(\\frac{C_{t,r}}{L_{t,r}}\\right)^{1-\\eta}.
    $$

    The regional values are then aggregated into yearly welfare:

    $$
    W_t = \\frac{L_t}{1-\\mu}
    \\left(\\frac{\\sum_r U_{t,r}}{L_t}\\right)^{
    \\frac{1-\\mu}{1-\\eta}}.
    $$

    A higher $\\eta$ gives relatively more weight to consumption changes in poorer regions.
    Setting $\\eta=0$ gives the same policy weighting as the cost-minimising setting, while
    setting $\\eta=\\mu$ gives the same policy weighting as the welfare-loss-minimising
    setting. The welfare levels can differ by terms that do not depend on the policy controls.

    <h3>Parameters defined in this module</h3>
    - param::elasmu
    - param::inequal_aversion

    """
    constraints = []

    # Parameters
    m.elasmu = Param(doc="::economics.elasmu")
    m.inequal_aversion = Param(doc="::economics.inequal_aversion")

    m.utility = Var(m.t, m.regions, initialize=10)
    m.yearly_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalEquation(
                m.utility,
                lambda m, t, r: calc_regional_utility(
                    m.consumption[t, r], m.population[t, r], m.inequal_aversion
                ),
            ),
            GlobalEquation(
                m.yearly_welfare,
                lambda m, t: sum(m.population[t, r] for r in m.regions)
                * calc_global_utility(
                    sum(m.utility[t, r] for r in m.regions),
                    m.global_population[t],
                    m.elasmu,
                    m.inequal_aversion,
                ),
            ),
        ]
    )

    return constraints


def calc_regional_utility(consumption, population, inequal_aversion):
    return population * soft_min(consumption / population) ** (1 - inequal_aversion)


def calc_global_utility(
    sum_regional_utility, global_population, elasmu, inequal_aversion
):
    return soft_min(sum_regional_utility / global_population) ** (
        (1 - elasmu) / (1 - inequal_aversion)
    ) / (1 - elasmu)
