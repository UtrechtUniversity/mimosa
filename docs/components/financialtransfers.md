---
icon: fontawesome/solid/money-bill-transfer
---

[:octicons-arrow-left-24: Back to general structure](index.md)

Besides [emission trading](emissiontrading.md), another mechanism to redistribute costs among regions is by allowing financial transfers
to compensate for damage costs. In MIMOSA, two types can be chosen: either no financial transfers (default), or a global damage cost pool.

The financial transfer module can be chosen using the parameter [`financialtransfer module`](../parameters.md#model.financialtransfer%20module).

Note that the difference with emission trading is that (paid for) emission reductions are not affected by any financial transfer from this module.

=== "No transfers `default`"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["financialtransfer module"] = "notransfer"
    model = MIMOSA(params)
    ```

    :::mimosa.components.financialtransfer.notransfer.get_constraints

=== "Global damage cost pool"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["financialtransfer module"] = "globaldamagepool"
    model = MIMOSA(params)
    ```

    :::mimosa.components.financialtransfer.globaldamagepool.get_constraints

