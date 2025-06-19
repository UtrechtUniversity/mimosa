# Running MIMOSA

### Base run
A basic run of MIMOSA requires 4 steps: loading the parameters, building the model instance, solving the model and finally saving the output.
With this code, the default parameter values are used (see [Parameter reference](parameters.md)).

``` python
--8<-- "tests/runs/run_base.py"
```

1.   Read the default parameters
2.   Build the model using the parameters
3.   Once the model is built, send the model to the solver.<br>
     Note that if you use the NEOS solver, use the syntax `model1.solve(use_neos=True, neos_email="your.email@email.com")`
4.   Export the output to the file output/run1.csv

### Reading the output

Once the script above has finished running, it has produced two output files in the folder `output`: `run1.csv` and `run1.csv.params.json`. The latter is simply a JSON file with all the input parameter used for this particular run (for reproducibility). The former is a CSV file that contains all the output data. Every variable in MIMOSA is saved in this value in a format similar to [IAMC data format](https://pyam-iamc.readthedocs.io/en/stable/data.html):

:fontawesome-solid-file-csv: `output/run1.csv`

{{ read_csv("docs/assets/data/run_cba.csv", nrows=3) }}
|... | ... |

These output files can be easily imported for plotting software (like using [Plotly](https://plotly.com/python/) in Python). An easier way, however, to quickly visualise and compare MIMOSA outputs, is by using the MIMOSA Dashboard. After opening the online Dashboard, simply drag and drop all output files to the drag-and-drop input to visualise one or multiple MIMOSA output files. Also include the parameter files to directly see the difference in input parameters.

[Open the MIMOSA Dashboard :octicons-arrow-right-24:](https://dashboard-mimosa.onrender.com/){.md-button}



### Changing parameters
The default parameters from `load_params()` are given as a nested dictionary. Every item of this dictionary can be changed. For a complete overview of all parameters that can be changed, see [Parameters](parameters.md).

#### Example 1: carbon budget

In this example, the [carbon budget](parameters.md#emissions.carbonbudget) is changed to 500 GtCO2. 

``` python hl_lines="4 5 6"
--8<-- "tests/runs/run_carbonbudget.py"
```

1.   Change the parameter of emissions > carbonbudget to the string "500 GtCO2"

#### Example 2: high damages, high TCRE, low discounting
Multiple parameters can also be changed at the same time. In this example, the high end of the [damages](parameters.md#economics.damages.quantile) and of the [climate sensitivity (TCRE)](parameters.md#temperature.TCRE) are used, combined with the low end of the [discount rate (PRTP)](parameters.md#economics.PRTP).

``` python hl_lines="4 5 6 7 8"
--8<-- "tests/runs/run_high_dmg_tcre_low_prtp.py"
```

### Doing multiple runs

Often, MIMOSA needs to be run with multiple values of the same parameter (multiple carbon budgets, multiple discount rates, etc.).
While it is possible to simply run the file multiple times, it is much easier to run MIMOSA multiple times directly in the Python script
through regular Python loops:


``` python hl_lines="3 7 12"
--8<-- "tests/runs/run_multipleruns.py"
```

1. Don't forget to save each file to a different name, otherwise they will be overwritten at each iteration of the loop.

### Doing a baseline run

It can be useful to do a MIMOSA run with zero mitigation: a baseline run. We distinguish two types of baseline runs: either with damages (a no-policy scenario, mainly to investigate the damages if no climate policy were implemented), and the true baseline run, in absence of climate policy and climate impacts.

Contrary to other scenarios, these are not optimisation runs, but rather simulation runs: the mitigation is set to zero, and the model is solved for the given parameters. Therefore, the `solve()` function is not used, but rather the `run_simulation()` or `run_nopolicy_baseline()` function. 

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



### Doing an effort-sharing run

MIMOSA has some built-in effort sharing regimes. In this example, they are used in combination with a carbon budget (but it could be used in CBA mode). The welfare module is set to cost minimising, as this is typically used with effort sharing regimes. Effort sharing would be impossible without emission trading. Finally, this would often be infeasible for some regions, if we didn't allow for some extra financial transfers beyond just emission trading, which is why we set the relative mitigation cost minimum level to a small negative number.

```python
--8<-- "tests/runs/run_effortsharing.py"
```

### Advanced: logging

The solve status (optimal, impossible, etc), model solve time and the final maximised value can be logged to an external log file (along with the warnings or errors from the code). This can be very useful when doing many runs overnight. In this code example, the log is written to the file `mainlog.log`:

``` python hl_lines="5 6 7 8 9 10 11 12 13"
--8<-- "tests/runs/run_logging.py"
```

1. By setting `verbose=False`, the IPOPT output is not printed.
     If you're doing many runs, this is probably useful. The termination status of IPOPT is
     logged to the log file anyway.