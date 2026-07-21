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
    params["model structure"]["effortsharing module"] = "equal_total_costs"
    model = MIMOSA(params)
    ```

    In this effort-sharing regime, the damages are also taken into account when equalising the costs among regions:

    $$
    \\text{mitigation costs}_{t,r} + \\text{damage costs}_{t,r}\\ (+ \\text{financial transfer}_{t,r}) = \\text{common level}_t,
    $$

    where the variable $\\text{common level}_t$ can have arbitrary values and is purely used as a common
    value accross all the regions[^1]. Note that the variable $\\text{damages}_{t,r}$ is already expressed as percentage of GDP (see [Damages](damages.md)).

    For feasibility reasons, this constraint is only enforced until 2100.

    Compared to the equal mitigation cost regime, this regime might be infeasible, especially for regions with very high damages, unless:

    * (a) the mitigation costs can be negative (for regions with very high damages). This can be achieved with the
        parameter [`rel_mitigation_costs_min_level`](../parameters.md#economics.MAC.rel_mitigation_costs_min_level).

    * or (b) if financial transfers are allowed between regions, that go beyond emission trading. See [Financial transfers](financialtransfers.md).

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
        # Total costs: mitigation + damage costs should be equal among regions as % GDP
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.mitigation_costs[t, r]
            + m.damage_costs[t, r]
            + m.financial_transfer[t, r],
            lambda m, t, r: m.effort_sharing_common_level[t],
            "effort_sharing_regime_total_costs",
            ignore_if=lambda m, t, r: m.year(t) > 2100,
        ),
    ]
