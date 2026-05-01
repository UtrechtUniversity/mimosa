The default parameters from `load_params()` are given as a nested dictionary. Every item of this dictionary can be changed. For a complete overview of all parameters that can be changed, see [Parameters](../parameters.md).

#### Example 1: carbon budget

In this example, the [carbon budget](../parameters.md#emissions.carbonbudget) is changed to 500 GtCO2. 

``` python hl_lines="4 5 6"
--8<-- "tests/runs/run_carbonbudget.py"
```

1.   Change the parameter of emissions > carbonbudget to the string "500 GtCO2"

#### Example 2: high damages, high TCRE, low discounting
Multiple parameters can also be changed at the same time. In this example, the high end of the [damages](../parameters.md#economics.damages.quantile) and of the [climate sensitivity (TCRE)](../parameters.md#temperature.TCRE) are used, combined with the low end of the [discount rate (PRTP)](../parameters.md#economics.PRTP).

``` python hl_lines="4 5 6 7 8"
--8<-- "tests/runs/run_high_dmg_tcre_low_prtp.py"
```
