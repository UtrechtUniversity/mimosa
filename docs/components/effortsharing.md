---
icon: fontawesome/solid/people-carry-box
---

[:octicons-arrow-left-24: Back to general structure](index.md)

Effort-sharing regimes can be used to enforce the redistribution of mitigation effort and damage costs among
regions following pre-defined equity principles. By default, in MIMOSA, no effort-sharing regime is imposed.

Besides no regime at all, there are five effort-sharing regimes implemented in MIMOSA. The regime can be
selected using the [`effortsharing module`](../parameters.md#model structure.effortsharing module) parameter.

=== "No regime `default`"

    :::mimosa.components.effortsharing.noregime.get_constraints

=== "Equal mitigation costs"

    :::mimosa.components.effortsharing.equal_mitigation_costs.get_constraints

=== "Equal total costs"

    :::mimosa.components.effortsharing.equal_total_costs.get_constraints

=== "Per capita convergence"

    :::mimosa.components.effortsharing.per_cap_convergence.get_constraints

=== "Ability to pay"

    :::mimosa.components.effortsharing.ability_to_pay.get_constraints

=== "Equal cumulative per capita emissions"

    :::mimosa.components.effortsharing.equal_cumulative_per_cap.get_constraints

??? note "Effort sharing in simulation mode"

    The example effort-sharing runs use optimisation. In simulation mode, the effort-sharing rules
    are not applied directly because they are constraints on calculated variables such as regional
    emission allowances and mitigation costs. A simulation can replay an optimised effort-sharing
    result when all underlying control values, including the relevant trading balances, are supplied,
    but it does not determine a new effort-sharing allocation itself.
