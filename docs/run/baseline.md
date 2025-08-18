It can be useful to do a MIMOSA run with zero mitigation: a baseline run. We distinguish two types of baseline runs: either with damages (a no-policy scenario, mainly to investigate the damages if no climate policy were implemented), and the true baseline run, in absence of climate policy and climate impacts.

Contrary to other scenarios, these are not optimisation runs, but rather simulation runs: the mitigation is set to zero, and the model is solved for the given parameters. Therefore, the `solve()` function is not used, but rather the `run_simulation()` or `run_nopolicy_baseline()` function. 

*Note: this requires MIMOSA version 0.2.0 or higher*

=== "No policy scenario with damages"

     ```python hl_lines="5 10 11 12"
     --8<-- "tests/runs/run_nopolicy_withdamages.py"
     ```

     1. This is default, so this line could be removed

=== "Baseline ignoring damages"

     ``` python hl_lines="5 6 11 12 13"
     --8<-- "tests/runs/run_baseline_nodamages.py"
     ```

     1. When damages are ignored, they do not affect the GDP. However, they are still calculated, and the variable `damage_costs` is still available in the output. To avoid this confusion, the damages are set to zero.

