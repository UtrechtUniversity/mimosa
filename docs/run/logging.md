The solve status (optimal, impossible, etc), model solve time and the final maximised value can be logged to an external log file (along with the warnings or errors from the code). This can be very useful when doing many runs overnight. In this code example, the log is written to the file `mainlog.log`:

``` python hl_lines="5 6 7 8 9 10 11 12 13"
--8<-- "tests/runs/run_logging.py"
```

1. By setting `verbose=False`, the IPOPT output is not printed.
     If you're doing many runs, this is probably useful. The termination status of IPOPT is
     logged to the log file anyway.