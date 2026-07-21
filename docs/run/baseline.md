It can be useful to run MIMOSA without mitigation: a baseline run. We distinguish two types: a no-policy scenario with damages, which shows the consequences of climate change without mitigation, and a baseline in which damages do not affect GDP.

These are simulation runs rather than optimisation runs. The model equations are evaluated with the control variables set to zero, without calling `solve()`. Use `run_nopolicy_baseline()` for both variants: besides returning the simulation result, it stores the no-policy damage costs used to calculate avoided damages in policy runs. See [Simulation and optimisation](simulation.md#use-case-1-create-a-no-policy-reference-run) for the difference between `run_nopolicy_baseline()` and the more general `run_simulation()` method.

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
