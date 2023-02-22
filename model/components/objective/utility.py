"""
Model equations and constraints:
Objective function
"""

from typing import Sequence, Tuple
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    Constraint,
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
    m.PRTP = Param()

    # Extra variable used to extend the objective function if necessary. By default,
    # this variable is equal to zero
    m.extra_NPV_objective = Var(m.t)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.NPV[t]
                == m.NPV[t - 1]
                + m.dt * exp(-m.PRTP * (m.year(t) - m.beginyear)) * m.yearly_welfare[t]
                + m.extra_NPV_objective[t]
                if t > 0
                else Constraint.Skip,
                name="NPV",
            ),
            GlobalInitConstraint(lambda m: m.NPV[0] == 0),
            GlobalConstraint(
                lambda m, t: m.extra_NPV_objective[t] == 0.0,
                name="empty_extra_NPV_objective",
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
