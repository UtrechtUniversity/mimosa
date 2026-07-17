# Logging runs

Logging is useful for long or unattended batches. MIMOSA records the solver status, solve time, save
messages, warnings and errors through Python's logging system. The following example appends these
messages to `mainlog.log`:

```python hl_lines="6 7 8 9 10 11 12"
--8<-- "tests/runs/run_logging.py"
```

1. `verbose=False` hides IPOPT's iteration output from the terminal. MIMOSA still writes its
   termination status and solve time to the configured Python log.

The model output is saved separately as `output/run1_logged.csv` with its parameter file. The log
does not replace the model output and does not currently include the final objective value.

## Points to keep in mind

- `mainlog.log` is created relative to the directory from which the script is run.
- `WatchedFileHandler` appends to an existing log, so repeated runs retain earlier messages.
- Running the setup code repeatedly in the same interactive Python session can attach the same
  handler more than once and duplicate messages. Configure logging once per process.
- `verbose=False` suppresses detailed IPOPT iterations; it does not redirect them into the Python
  log. To retain a separate IPOPT log, pass `ipopt_output_file="ipopt.log"` to `solve()`.
