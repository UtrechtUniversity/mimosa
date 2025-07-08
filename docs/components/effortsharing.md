---
icon: fontawesome/solid/people-carry-box
---

[:octicons-arrow-left-24: Back to general structure](index.md)

Effort-sharing regimes can be used to enforce the redistribution of mitigation effort and damage costs among
regions following pre-defined equity principles. By default, in MIMOSA, no effort-sharing regime is imposed.

Besides no regime at all, there are three types of effort-sharing regimes implemented in MIMOSA. This can be
set using the [`effort_sharing_regime`](../parameters.md#effort sharing.regime) parameter.

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

