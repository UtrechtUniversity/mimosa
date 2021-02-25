"""
Model equations and constraints:
Objective function
"""

from model.common.pyomo import (
    Param,
    Var,
    GlobalConstraint,
    GlobalInitConstraint,
    Constraint,
    Objective,
    exp,
    maximize,
)


def get_constraints(m):
    """Equations and constraints for the objective of the optimisation
    (utility specification)

    Necessary variables:
        -

    Returns:
        - Objective
        - list of constraints (GlobalConstraint, GlobalInitConstraint, RegionalConstraint, RegionalInitConstraint)
    """
    constraints = []

    m.NPV = Var(m.t)
    m.PRTP = Param()
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.NPV[t]
                == m.NPV[t - 1]
                + m.dt
                * exp(-m.PRTP * (m.year(t) - m.beginyear))
                * sum(m.L(m.year(t), r) * m.utility[t, r] for r in m.regions)
                if t > 0
                else Constraint.Skip,
                name="NPV",
            ),
            GlobalInitConstraint(lambda m: m.NPV[0] == 0),
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
