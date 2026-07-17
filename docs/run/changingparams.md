# Changing parameters

`load_params()` returns the default configuration as a nested dictionary. Change values in this
dictionary before creating `MIMOSA(params)`. This is useful for policy scenarios, sensitivity
analysis and alternative model assumptions. The [parameter reference](../parameters.md) lists all
available settings, their defaults and accepted values.

## Example 1: impose a carbon budget

The default configuration performs cost-benefit analysis without a fixed carbon budget. This example
instead limits cumulative emissions to 500 GtCO2:

```python hl_lines="5"
--8<-- "tests/runs/run_carbonbudget.py"
```

1. Quantities must include a compatible unit. MIMOSA converts the value to its standard
   [emissions unit](../extending/units.md).

The optimisation result is saved as `output/run_example_carbonbudget.csv`, together with
`output/run_example_carbonbudget.csv.params.json` containing the configuration used for the run.

## Example 2: change several assumptions

Several parameters can be changed before constructing one model. This example combines the 95th
percentile damage functions, a high TCRE and a low pure rate of time preference:

```python hl_lines="5 6 7"
--8<-- "tests/runs/run_high_dmg_tcre_low_prtp.py"
```

The resulting files are saved under `output/run_example2.csv`.

!!! tip "Start each scenario from fresh defaults"

    Call `load_params()` separately for each scenario. This prevents changes made for one scenario
    from unintentionally carrying over to another. Parameters are checked and converted when
    `MIMOSA(params)` is created; changing the original dictionary afterward does not update an
    existing model.

!!! warning "Use the expected value type"

    Dimensionless settings such as `PRTP` use numbers, while physical quantities such as TCRE and
    carbon budgets use strings containing units. Invalid paths, unknown settings and incompatible
    units produce a configuration error when the model is created.
