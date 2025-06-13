"""
Model equations and constraints:
Objective function
"""

from typing import Sequence, Tuple
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalEquation,
    Objective,
    exp,
    maximize,
)


def get_constraints(m: AbstractModel) -> Tuple[Objective, Sequence[GeneralConstraint]]:
    """Equations and constraints for the objective of the optimisation
    (utility specification)

    Necessary variables:
        -

    Returns:
        - Objective
        - list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.NPV = Var(m.t)
    m.PRTP = Param(doc="::economics.PRTP")
    constraints.extend(
        [
            GlobalEquation(
                m.NPV,
                lambda m, t: (
                    m.NPV[t - 1]
                    + m.dt
                    * exp(-m.PRTP * (m.year(t) - m.beginyear))
                    * m.yearly_welfare[t]
                    if t > 0
                    else 0
                ),
            ),
        ]
    )

    ## If carbon budget is a soft constraint (not in use now):

    # m.obj = Objective(rule=lambda m: m.NPV[m.tf] * (
    #     soft_switch(m.budget-(
    #         m.cumulative_emissions[m.year2100]
    #         + sum(soft_min(m.global_emissions[t]) for t in m.t if m.year(t) >= 2100)
    #     ), scale=1)
    # ), sense=maximize)

    objective = Objective(rule=lambda m: m.NPV[m.tf], sense=maximize)

    return objective, constraints
