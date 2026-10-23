"""
Model equations and constraints:
Utility and global welfare
"""

from typing import Sequence

from mimosa.common import (
    ConcreteModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    soft_min,
)

from mimosa.core.model_inputs import ModelInputs


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""
    <h3>General inequality aversion</h3>

    This setting makes the weight given to inequality between regions explicit. Let $\href{./#var__welfare_inequal_aversion_general::consumption}{C_{t,r}}$
    be regional consumption, $\href{./#param__timeandregional.population}{L_{t,r}}$ population, $\href{./#param__economics.inequal_aversion}{\eta}$ the inequality-aversion parameter
    (`inequal_aversion`), and $\href{./#param__economics.elasmu}{\mu}$ the elasticity of marginal utility (`elasmu`). MIMOSA first
    calculates:

    $$
    \href{./#var__welfare_inequal_aversion_general::utility}{U_{t,r}} = \href{./#param__timeandregional.population}{L_{t,r}}
    \left(\frac{\href{./#var__welfare_inequal_aversion_general::consumption}{C_{t,r}}}{\href{./#param__timeandregional.population}{L_{t,r}}}\right)^{1-\href{./#param__economics.inequal_aversion}{\eta}}.
    $$

    The regional values are then aggregated into yearly welfare:

    $$
    \href{./#var__welfare_inequal_aversion_general::global_welfare}{W_t} = \frac{L_t}{1-\href{./#param__economics.elasmu}{\mu}}
    \left(\frac{\sum_r \href{./#var__welfare_inequal_aversion_general::utility}{U_{t,r}}}{L_t}\right)^{
    \frac{1-\href{./#param__economics.elasmu}{\mu}}{1-\href{./#param__economics.inequal_aversion}{\eta}}}.
    $$

    A higher $\href{./#param__economics.inequal_aversion}{\eta}$ gives relatively more weight to consumption changes in poorer regions.
    Setting $\href{./#param__economics.inequal_aversion}{\eta}=0$ gives the same policy weighting as the cost-minimising setting, while
    setting $\href{./#param__economics.inequal_aversion}{\eta}=\href{./#param__economics.elasmu}{\mu}$ gives the same policy weighting as the welfare-loss-minimising
    setting. The welfare levels can differ by terms that do not depend on the policy controls.

    <h3>Parameters defined in this module</h3>
    - param::elasmu
    - param::inequal_aversion

    """
    constraints = []

    # Parameters
    m.elasmu = Param(initialize=inputs.config("economics.elasmu"))
    m.inequal_aversion = Param(initialize=inputs.config("economics.inequal_aversion"))

    m.utility = Var(m.t, m.regions, initialize=10)
    m.global_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalEquation(
                m.utility,
                lambda m, t, r: calc_regional_utility(
                    m.consumption[t, r], m.population[t, r], m.inequal_aversion
                ),
            ),
            GlobalEquation(
                m.global_welfare,
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
