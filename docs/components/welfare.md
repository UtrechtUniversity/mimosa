[:octicons-arrow-left-24: Back to general structure](general.md)

## Welfare and utility

The optimisation goal of MIMOSA is to maximise discounted welfare or utility[^1]. There are three ways to calculate welfare in MIMOSA: welfare-loss-minimising, cost-minimising, and a general inequality aversion setting which is the generalised version of the first two methods.

The welfare module can be chosen using the parameter `params["model"]["welfare module"]`.


=== "Welfare-loss-minimising `default`"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["welfare module"] = "welfare_loss_minimising"
    model = MIMOSA(params)
    ```

    :::mimosa.components.welfare.welfare_loss_minimising.get_constraints

=== "Cost-minimising"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["welfare module"] = "cost_minimising"
    model = MIMOSA(params)
    ```

    :::mimosa.components.welfare.cost_minimising.get_constraints

=== "General inequality aversion"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model"]["welfare module"] = "inequal_aversion_general"
    model = MIMOSA(params)
    ```

    :::mimosa.components.welfare.inequal_aversion_general.get_constraints



## Optimisation goal and discounting

TODO

[^1]: While the terms welfare and utility can be used interchangeably, we typically refer to *utility* as the regional utility, and *welfare* as the global population-weighted utility.