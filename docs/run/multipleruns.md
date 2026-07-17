# Running multiple scenarios

Use a normal Python loop when the same model setup should be solved for several parameter values, for
example a range of carbon budgets or discount rates:

```python hl_lines="3 7 12"
--8<-- "tests/runs/run_multipleruns.py"
```

1. Every run needs a unique output name. Otherwise a later iteration overwrites the CSV and parameter
   file from an earlier run.

This example performs three sequential optimisations and creates one CSV and one `.params.json` file
for each carbon budget. The files can be loaded together in the MIMOSA Dashboard to compare the
scenarios.

## Points to keep in mind

- Call `load_params()` inside the loop so that every scenario starts from the same defaults.
- Include the varied value in the output name, and use a filename-safe label for more complicated
  parameter values.
- The loop stops if model construction or optimisation raises an error. For a large unattended
  experiment, add [logging](logging.md) and decide explicitly whether a failed scenario should stop
  the remaining runs.
- This pattern runs scenarios one after another. It does not run them in parallel.
