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
    params["effort sharing"]["regime"] = "equal_total_costs"
    model = MIMOSA(params)
    ```

    In this effort-sharing regime, the damages are also taken into account when equalising the costs among regions:

    $$
    \\frac{\\text{mitig. costs}_{t,r}}{\\text{GDP}_{\\text{gross},t,r}} + \\text{damages}_{t,r}\\ (+ \\text{rel. financial transf.}_{t,r}) = \\text{common level}_t,
    $$

    where the variable $\\text{common level}_t$ can have arbitrary values and is purely used as a common
    value accross all the regions[^1]. Note that the variable $\\text{damages}_{t,r}$ is already expressed as percentage of GDP (see [Damages](damages.md)).

    For feasibility reasons, this constraint is only enforced until 2100.

    Compared to the equal mitigation cost regime, this regime might be infeasible, especially for regions with very high damages, unless:

    * (a) the mitigation costs can be negative (for regions with very high damages). This can be achieved with the
        parameter [`rel_mitigation_costs_min_level`](../parameters.md#economics.MAC.rel_mitigation_costs_min_level).

    * or (b) if financial transfers are allowed between regions, that go beyond emission trading. See [Financial transfers](financialtransfers.md).

    [^1]: Note that for numerical stability, the constraint is not implemented as an equality constraint,
        but as an "almost-equality" constraint (called soft-equality constraint). This means that it is enough
        if the left-hand side (LHS) and right-hand side (RHS) are very close to each other (less than 0.5%):

        $$
        0.995 \\cdot \\text{LHS} \\leq \\text{RHS} \\leq 1.005 \\cdot \\text{LHS}.
        $$
    """

    m.effort_sharing_common_level = Var(m.t, units=quant.unit("fraction_of_GDP"))

    return [
        # Total costs: mitigation + damage costs should be equal among regions as % GDP
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.rel_mitigation_costs[t, r]
            + m.damage_costs[t, r]
            + m.rel_financial_transfer[t, r],
            lambda m, t, r: m.effort_sharing_common_level[t],
            "effort_sharing_regime_total_costs",
            ignore_if=lambda m, t, r: m.year(t) > 2100,
        ),
    ]
