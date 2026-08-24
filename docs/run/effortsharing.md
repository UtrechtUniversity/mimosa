# Running effort-sharing scenarios

Use an [effort-sharing regime](../components/effortsharing.md) when a carbon budget or cost-benefit
run should also follow a regional allocation rule. The example below loops over the five available
regimes and solves a separate optimisation for each one:

```python
--8<-- "tests/runs/run_effortsharing.py"
```

1. Using the exogenous SSP baseline emissions prevents regional baseline emissions from changing
   with damage-induced GDP losses.
2. A negative minimum allows regions receiving trading payments to have negative attributed
   mitigation costs.

The example combines each regime with the following settings:

| Setting                   | Purpose                                                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `emissiontrade`           | Allows attributed emission reductions and costs to differ from the reductions physically taking place in a region |
| `cost_minimising` welfare | Uses equal monetary cost weighting while the selected regime determines the regional allocation                   |
| 700 GtCO2 carbon budget   | Gives all five runs the same global mitigation target                                                             |

Five output pairs are created, named `run_<regime>.csv` and
`run_<regime>.csv.params.json`. Useful variables for comparing the results include
`regional_emission_allowances`, `attributed_emission_reductions`,
`mitigation_cost_trading_balance` and `mitigation_costs`.

## Points to keep in mind

- Some regimes require large transfers and can otherwise be infeasible. The value
  `rel_mitigation_costs_min_level = -0.5` is a permissive assumption for this comparison, not a
  universal recommended value.
- Effort-sharing rules use soft equalities, so the allocation is satisfied within its documented
  tolerance rather than as an exact numerical equality.
- Keeping baseline emissions exogenous can improve numerical behaviour in these comparisons, but it
  also changes the model assumption: baseline emissions no longer respond to lower GDP.
- These examples use optimisation. See the note on the [effort-sharing component
  page](../components/effortsharing.md) for the limitation in simulation mode.
