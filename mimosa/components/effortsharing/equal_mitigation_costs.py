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
    ModelContext,
)


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["effortsharing module"] = "equal_mitigation_costs"
    model = MIMOSA(params)
    ```

    Equal mitigation costs implies that the attributed mitigation costs in every year (in terms of
    percentage of GDP) should be the same for every region:

    $$
    \\text{mitigation costs}_{t,r} = \\text{common level}_t,
    $$

    where the variable $\\text{common level}_t$ can have arbitrary values and is purely used as a common
    value accross all the regions[^1].

    [^1]: Implementing every regional condition as an exact equality can give IPOPT too many or
        redundant equality equations relative to the available variables. The condition is therefore
        implemented as an "almost-equality" (a soft-equality constraint), allowing a difference of at
        most 0.5%. See [Soft-equality constraints](../extending/variables_constraints.md#soft-equality-constraints).

        $$
        0.995 \\cdot \\text{RHS} \\leq \\text{LHS} \\leq 1.005 \\cdot \\text{RHS}.
        $$

    """

    m.effort_sharing_common_level = Var(m.t, units=quant.unit("fraction_of_GDP"))

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.mitigation_costs[t, r],
            lambda m, t, r: m.effort_sharing_common_level[t],
            "effort_sharing_regime_mitigation_costs",
        ),
    ]
