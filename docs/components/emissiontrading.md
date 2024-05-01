---
icon: material/earth
---

[:octicons-arrow-left-24: Back to general structure](index.md)

By default, every region has to pay for their own emission reductions. However, emission trading is a mechanism to allow regions to trade emission allowances with each other. This way, regions can pay for reductions in other regions if it is cheaper than reducing their own emissions or when following an effort-sharing regime.

The emission trading module can be chosen using the parameter [`emissiontrade module`](../parameters.md#model.emissiontrade%20module).

Note that emission trading is most often used in combination with an [effort-sharing module](effortsharing.md).

=== "No emission trade `default`"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["emissiontrade module"] = "notrade"
    model = MIMOSA(params)
    ```

    :::mimosa.components.emissiontrade.notrade.get_constraints

=== "With emission trade"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["emissiontrade module"] = "emissiontrade"
    model = MIMOSA(params)
    ```

    :::mimosa.components.emissiontrade.emissiontrade.get_constraints

