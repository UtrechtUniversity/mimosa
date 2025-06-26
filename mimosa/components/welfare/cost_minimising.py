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
)
from .utility_fct import calc_utility


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    <h3>Cost-minimising setting</h3>

    In cost-minimising setting, the global per-capita consumption is first calculated before
    applying the utility function. This means that costs are weighted equally across regions,
    regardless of the regional per capita consumption. As a consequence, this setting leads to
    uniform carbon prices across regions. This is quantitatively similar to using Negishi weights.

    ???+ info "Difference with welfare-loss-minimising setting"
        In the welfare-loss-minimising setting, the utility function is applied to the regional
        per capita consumption values, and the regional utilities are then summed up to get the
        global welfare. This means that costs (from mitigation or damages) have a larger weight in
        the final welfare in poorer regions than in richer regions.


    <h3>Equations</h3>

    First, calculate the global consumption $C_{t,r}$ and population $L_{t,r}$:

    $$ \\widehat{C}_{t} = \\sum_r C_{t,r}, $$

    $$ \\widehat{L}_{t} = \\sum_r L_{t,r}. $$

    These are used to calculate the global utility:

    $$ W_t = \\widehat{L}_t \\cdot \\text{utility}\\left( \\widehat{C}_{t}, \\widehat{L}_{t} \\right) $$

    <h3>Utility function</h3>
    :::mimosa.components.welfare.utility_fct.calc_utility


    <h3>Parameters defined in this module</h3>
    - param::elasmu

    """
    constraints = []

    # Parameters
    m.elasmu = Param(doc="::economics.elasmu")

    m.utility = Var(m.t, m.regions, initialize=10)
    m.yearly_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalEquation(
                m.utility, lambda m, t, r: m.consumption[t, r] / m.population[t, r]
            ),
            GlobalEquation(
                m.yearly_welfare,
                lambda m, t: m.global_population[t]
                * calc_utility(
                    sum(m.consumption[t, r] for r in m.regions),
                    sum(m.population[t, r] for r in m.regions),
                    m.elasmu,
                ),
            ),
        ]
    )

    return constraints
