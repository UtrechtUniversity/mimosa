---
icon: material/earth
---

[:octicons-arrow-left-24: Back to general structure](index.md)

Without emission trading, the reductions and mitigation costs attributed to a region are the reductions and costs that physically occur within that region. Emission trading allows this attribution to differ, for example because reductions are cheaper elsewhere or because an [effort-sharing regime](effortsharing.md) assigns a different distribution of emission allowances.

The emission trading module can be chosen using the parameter [`emissiontrade module`](../parameters.md#model structure.emissiontrade module).

## Physical and attributed reductions and costs

Emission trading distinguishes between where an emission reduction takes place and the region to which the reduction and its cost are attributed:

- `regional_emission_reductions` is the physical reduction within a region.
- `attributed_emission_reductions` is the reduction attributed to a region after trading.
- `domestic_mitigation_costs_abs` is the cost of the physical reductions within a region.
- `mitigation_costs_abs` is the cost attributed to a region after trading.

With emission trading, the two pairs are connected through the trading balances:

$$
\begin{align}
\text{attributed emission reductions}_{t,r}
    &= \text{regional emission reductions}_{t,r}
       + \text{emission reduction trading balance}_{t,r},\\
\text{mitigation costs abs}_{t,r}
    &= \text{domestic mitigation costs abs}_{t,r}
       + \text{mitigation cost trading balance}_{t,r}.
\end{align}
$$

A positive trading balance means that a region buys reductions and pays other regions. A negative balance means that a region sells reductions and receives payment. Without emission trading, both balances are zero, so physical and attributed reductions and costs are the same.

## Variables in the model results

| Variable                             | Meaning                                                                                  | Unit                           | Availability                            |
| ------------------------------------ | ---------------------------------------------------------------------------------------- | ------------------------------ | --------------------------------------- |
| `regional_emission_reductions`       | Physical emission reduction within the region                                            | Emissions per year             | Both options                            |
| `attributed_emission_reductions`     | Emission reductions attributed to the region after trading                               | Emissions per year             | Emission trading only                   |
| `emission_reduction_trading_balance` | Reductions bought (positive) or sold (negative) by the region                            | Emissions per year             | Both options; always zero without trade |
| `regional_emission_allowances`       | Emissions assigned to the region after accounting for its attributed reductions          | Emissions per year             | Both options                            |
| `domestic_mitigation_costs_abs`      | Cost of reductions taking place within the region                                        | Currency per year              | Both options                            |
| `mitigation_costs_abs`               | Mitigation costs attributed to the region after trading                                  | Currency per year              | Both options                            |
| `mitigation_cost_trading_balance`    | Payments made (positive) or received (negative) by the region                            | Currency per year              | Both options; always zero without trade |
| `carbon_price`                       | Marginal carbon price in a region                                                        | Currency per unit of emissions | Both options                            |
| `global_carbon_price`                | Population-weighted average carbon price used to convert payments into traded reductions | Currency per unit of emissions | Emission trading only                   |

The exact units are determined by the configured [model units](../extending/units.md). With the default units, emissions flows are expressed per year and costs are expressed in trillion 2010 US dollars per year.

## Checking emission-trading results

For every timestep with emission trading, the payments sum to zero across regions:

$$
\sum_r \text{mitigation cost trading balance}_{t,r} = 0.
$$

Because all payments are converted at the same global carbon price, the emission reduction trading balances also sum to zero. Therefore, trading changes the regional attribution of reductions and costs, but not their global totals. Small non-zero sums can occur in numerical results because of solver tolerances.

The regional emission allowances are calculated from the reductions attributed to a region:

$$
\text{regional emission allowances}_{t,r}
    = \text{baseline emissions}_{t,r}
      - \text{attributed emission reductions}_{t,r}.
$$

Without emission trading, `regional_emission_allowances` is simply equal to `regional_emissions`.

## Interaction with other modules

Emission trading is often used with an [effort-sharing module](effortsharing.md). Effort sharing determines how allowances or costs should be distributed among regions, while emission trading connects that distribution to the physical reductions and costs in each region.

The [financial transfer module](financialtransfers.md) is separate. Its transfers redistribute damage costs and do not change `attributed_emission_reductions`, `regional_emission_allowances`, or either emission-trading balance.

## Available options

=== "No emission trade `default`"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["emissiontrade module"] = "notrade"
    model = MIMOSA(params)
    ```

    :::mimosa.components.emissiontrade.notrade.get_constraints

=== "With emission trade"

    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["emissiontrade module"] = "emissiontrade"
    model = MIMOSA(params)
    ```

    :::mimosa.components.emissiontrade.emissiontrade.get_constraints
