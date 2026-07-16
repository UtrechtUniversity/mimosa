---
icon: material/arrow-projectile-multiple
---

[:octicons-arrow-left-24: Back to general structure](index.md)

## Welfare and utility

MIMOSA separates the calculation of yearly welfare[^1] from the final optimisation goal. There are three ways to calculate welfare: welfare-loss-minimising, cost-minimising, and a general inequality-aversion setting that connects the first two methods. The objective can then either maximise discounted welfare or minimise discounted global costs.

The welfare module can be chosen using the parameter [`welfare module`](../parameters.md#model structure.welfare module).


=== "Welfare-loss-minimising `default`"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["welfare module"] = "welfare_loss_minimising"
    model = MIMOSA(params)
    ```

    :::mimosa.components.welfare.welfare_loss_minimising.get_constraints

=== "Cost-minimising"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["welfare module"] = "cost_minimising"
    model = MIMOSA(params)
    ```

    :::mimosa.components.welfare.cost_minimising.get_constraints

=== "General inequality aversion"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["welfare module"] = "inequal_aversion_general"
    model = MIMOSA(params)
    ```

    :::mimosa.components.welfare.inequal_aversion_general.get_constraints



## Optimisation goal and discounting

The welfare module determines how regional consumption is aggregated into `yearly_welfare`. The separate [`objective module`](../parameters.md#model structure.objective module) determines what MIMOSA optimises:

- `utility` (default) maximises discounted `yearly_welfare`.
- `globalcosts` minimises discounted mitigation and damage costs.

The objective can be selected in the model configuration:

```python
params = load_params()
params["model structure"]["objective module"] = "globalcosts"
model = MIMOSA(params)
```

With the utility objective, MIMOSA calculates:

$$
\text{NPV}_t =
\text{NPV}_{t-1}
+ \Delta t \cdot e^{-\text{PRTP}(\text{year}_t-\text{begin year})}
\cdot \text{yearly welfare}_t,
$$

This is a discrete approximation of the integral of discounted yearly welfare from the beginning year $t_0$ to the final year $T$:

$$
\text{NPV}(T) =
\int_{t_0}^{T}
e^{-\text{PRTP}(t-t_0)} \cdot \text{yearly welfare}(t)\, dt.
$$

MIMOSA maximises the final value of `NPV`. With the global-cost objective, `yearly_welfare` is replaced by:

$$
\text{global costs}_t =
\sum_r \left(
\text{mitigation costs}_{t,r}
+ \text{damage costs}_{t,r} \cdot \text{GDP gross}_{t,r}
\right),
$$

and the final `NPV` is minimised. The welfare variables are still calculated in this case, but they do not determine the objective.

[`PRTP`](../parameters.md#economics.PRTP) is the pure rate of time preference. A higher value gives less weight to outcomes further in the future. The factor $\Delta t$ accounts for the number of years represented by each timestep.

The main result variables are:

| Variable | Meaning |
| --- | --- |
| `utility` | Regional utility or consumption measure, depending on the selected welfare module |
| `yearly_welfare` | Welfare aggregated across regions for one timestep |
| `NPV` | Discounted welfare under the utility objective, or discounted costs under the global-cost objective |

[^1]: While the terms welfare and utility can be used interchangeably, we typically refer to *utility* as the regional utility, and *welfare* as the global population-weighted utility.
