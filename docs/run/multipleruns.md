Often, MIMOSA needs to be run with multiple values of the same parameter (multiple carbon budgets, multiple discount rates, etc.).
While it is possible to simply run the file multiple times, it is much easier to run MIMOSA multiple times directly in the Python script
through regular Python loops:


``` python hl_lines="3 7 12"
--8<-- "tests/runs/run_multipleruns.py"
```

1. Don't forget to save each file to a different name, otherwise they will be overwritten at each iteration of the loop.