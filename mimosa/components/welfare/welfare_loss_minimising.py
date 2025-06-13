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
    GlobalEquation,
    RegionalEquation,
)
from .utility_fct import calc_utility


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    <h3>Welfare-loss-minimising setting</h3>

    In welfare-loss-minimising setting, the utility is first calculated regionally
    from the per capita consumption. These regional utilities are then summed up to
    get the global welfare. This means that costs are weighted differently in different
    regions, depending on the regional per capita consumption. As a consequence, this
    setting leads to differentiated carbon prices across regions: poorer regions typically
    will have lower carbon prices than richer regions.

    ???+ info "Difference with cost-minimising setting"
        In the cost-minimising setting, the regional per capita consumption values
        are first added up to a global per capita consumption. The utility function
        is only then applied to this global per capita consumption to obtain global welfare.

    <h3>Equations</h3>

    First, calculate the regional utility using the regional consumption $C_{t,r}$ and population $L_{t,r}$:
    $$ U_{t,r} = \\text{utility}(C_{t,r}, L_{t,r}) $$

    Second, the global welfare is calculated as the sum of the regional utility values weighted by population:
    $$ W_t = \\sum_r L_{t,r} \\cdot U_{t,r} $$

    <h3>Utility function</h3>
    :::mimosa.components.welfare.utility_fct.calc_utility


    <h3>Parameters defined in this module</h3>
    - param::elasmu

    """
    constraints = []

    # Parameters
    m.elasmu = Param(doc="::economics.elasmu")

    m.utility = Var(m.t, m.regions, initialize=0.1)
    m.yearly_welfare = Var(m.t)

    constraints.extend(
        [
            RegionalEquation(
                m.utility,
                lambda m, t, r: calc_utility(
                    m.consumption[t, r], m.population[t, r], m.elasmu
                ),
            ),
            GlobalEquation(
                m.yearly_welfare,
                lambda m, t: sum(
                    m.population[t, r] * m.utility[t, r] for r in m.regions
                ),
            ),
        ]
    )

    return constraints
