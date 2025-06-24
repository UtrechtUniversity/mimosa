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
    params["effort sharing"]["regime"] = "equal_mitigation_costs"
    model = MIMOSA(params)
    ```

    Equal mitigation costs implies that the regional mitigation costs in every year (in terms of
    percentage of GDP) should be the same for every region:

    $$
    \\frac{\\text{mitig. costs}_{t,r}}{\\text{GDP}_{\\text{gross},t,r}} = \\text{common level}_t,
    $$

    where the variable $\\text{common level}_t$ can have arbitrary values and is purely used as a common
    value accross all the regions[^1].

    [^1]: Note that for numerical stability, the constraint is not implemented as an equality constraint,
        but as an "almost-equality" constraint (called soft-equality constraint). This means that it is enough
        if the left-hand side (LHS) and right-hand side (RHS) are very close to each other (less than 0.5%):

        $$
        0.995 \\cdot \\text{LHS} \\leq \\text{RHS} \\leq 1.005 \\cdot \\text{LHS}.
        $$

    """

    m.effort_sharing_common_level = Var(m.t, units=quant.unit("fraction_of_GDP"))

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.rel_mitigation_costs[t, r],
            lambda m, t, r: m.effort_sharing_common_level[t],
            "effort_sharing_regime_mitigation_costs",
        ),
    ]
