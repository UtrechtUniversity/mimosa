# Running MIMOSA

### Base run
A basic run of MIMOSA requires 4 steps: loading the parameters, building the model instance, solving the model and finally saving the output.
With this code, the default parameter values are used (see [Parameter reference](parameters.md)).

``` python
from mimosa import MIMOSA, load_params

params = load_params()  # (1)!

model1 = MIMOSA(params) # (2)!
model1.solve() # (3)!

model1.save("run1") # (4)!
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

> **Note:** the MIMOSA Dashboard can sometimes take up to a few minutes to start, as it goes to sleep after 30 minutes of inactivity (restriction of the free plan of the hosting website).

[Open the MIMOSA Dashboard :octicons-arrow-right-24:](https://dashboard-mimosa.onrender.com/){.md-button}



### Changing parameters
The default parameters from `load_params()` are given as a nested dictionary. Every item of this dictionary can be changed. Note that only the values can be changed, it is not possible to add or substract parameters to this dictionary (without [Extending MIMOSA](extending/general.md)).

#### Example 1: carbon budget

``` python hl_lines="4 5 6"
from mimosa import MIMOSA, load_params

params = load_params()

params["emissions"]["carbonbudget"] = "500 GtCO2" # (1)!

model1 = MIMOSA(params)
model1.solve()

model1.save("run_example1")
```

1.   Change the parameter of emissions > carbonbudget to the string "500 GtCO2"

#### Example 2: high damages, high TCRE, low discounting
Multiple parameters can also be changed at the same time. In this example, the high end of the [damages](parameters.md#economics.damages.quantile) and of the [climate sensitivity (TCRE)](parameters.md#temperature.TCRE) are used, combined with the low end of the [discount rate (PRTP)](parameters.md#economics.PRTP).

``` python hl_lines="4 5 6 7 8"
from mimosa import MIMOSA, load_params

params = load_params()

params["economics"]["damages"]["quantile"] = 0.95
params["temperature"]["TCRE"] = "0.82 delta_degC/(TtCO2)"
params["economics"]["PRTP"] = 0.001

model2 = MIMOSA(params)
model2.solve()

model2.save("run_example2")
```

### Doing multiple runs

Often, MIMOSA needs to be run with multiple values of the same parameter (multiple carbon budgets, multiple discount rates, etc.).
While it is possible to simply run the file multiple times, it is much easier to run MIMOSA multiple times directly in the Python script
through regular Python loops:


``` python hl_lines="3 7 12"
from mimosa import MIMOSA, load_params

for budget in ["500 GtCO2", "700 GtCO2", "1000 GtCO2"]:

     params = load_params()

     params["emissions"]["carbonbudget"] = budget

     model3 = MIMOSA(params)
     model3.solve()

     model3.save(f"run_example3_{budget}") # (1)!
```

1. Don't forget to save each file to a different name, otherwise they will be overwritten at each iteration of the loop.

### Doing a baseline run

It can be useful to do a MIMOSA run with zero mitigation: a baseline run. We distinguish two types of baseline runs: either ignoring damages (the true baseline run, in absence of climate policy and climate impacts), or with damages (a no-policy scenario, mainly to investigate the damages if no climate policy were implemented).

=== "Baseline ignoring damages"

     ``` python hl_lines="4 5 6 7"
     from mimosa import MIMOSA, load_params

     params = load_params()

     params["emissions"]["carbonbudget"] = False
     params["economics"]["damages"]["ignore damages"] = True
     
     params["model"]["welfare module"] = "cost_minimising"

     # Disable some emission reduction constraints
     params["emissions"]["non increasing emissions after 2100"] = False
     params["emissions"]["not positive after budget year"] = False
     params["emissions"]["inertia"]["regional"] = False
     params["emissions"]["inertia"]["global"] = False

     params["time"]["end"] = 2150

     model = MIMOSA(params)
     model.solve()
     model.save("baseline_ignore_damages")
     ```

=== "No policy scenario with damages"

     ```python hl_lines="9 10 11 12 13 14 15 16 17"
     from mimosa import MIMOSA, load_params

     params = load_params()

     params["emissions"]["carbonbudget"] = False
     params["economics"]["damages"]["ignore damages"] = False # (1)!
     params["model"]["welfare module"] = "cost_minimising"

     # Force the mitigation effort to be zero
     params["simulation"]["simulationmode"] = True
     params["simulation"]["constraint_variables"] = {
          "relative_abatement": {
               year: {region: 0.0 for region in params["regions"]}
               for year in range(2025, 2151, 5)
          },
     }
     params["economics"]["MAC"]["gamma"] = "0.00001 USD2005/tCO2" # (2)!

     # Disable some emission reduction constraints
     params["emissions"]["non increasing emissions after 2100"] = False
     params["emissions"]["not positive after budget year"] = False
     params["emissions"]["inertia"]["regional"] = False
     params["emissions"]["inertia"]["global"] = False

     params["time"]["end"] = 2150

     model = MIMOSA(params)
     model.solve()
     model.save("baseline_no_policy")
     ```

     1. This is default, so this line could be removed
     2. Needed for numerical stability


### Doing an effort-sharing run

MIMOSA has some built-in effort sharing regimes. In this example, they are used in combination with a carbon budget (but it could be used in CBA mode). The welfare module is set to cost minimising, as this is typically used with effort sharing regimes. Effort sharing would be impossible without emission trading. Finally, this would often be infeasible for some regions, if we didn't allow for some extra financial transfers beyond just emission trading, which is why we set the relative mitigation cost minimum level to a small negative number.

```python
from mimosa import MIMOSA, load_params


# Loop over the three available effort sharing regimes
for regime in [
     "equal_mitigation_costs",
     "equal_total_costs",
     "per_cap_convergence",
]:
     params = load_params()
     params["model"]["emissiontrade module"] = "emissiontrade"
     params["model"]["welfare module"] = "cost_minimising"
     params["emissions"]["carbonbudget"] = "700 GtCO2"
     params["effort sharing"]["regime"] = regime
     params["economics"]["MAC"]["rel_mitigation_costs_min_level"] = -0.3
     params["time"]["end"] = 2100

     model1 = MIMOSA(params)
     model1.solve()
     model1.save(f"run_{regime}")

```

### Advanced: logging

The solve status (optimal, impossible, etc), model solve time and the final maximised value can be logged to an external log file (along with the warnings or errors from the code). This can be very useful when doing many runs overnight. In this code example, the log is written to the file `mainlog.log`:

``` python hl_lines="5 6 7 8 9 10 11 12 13"
import logging
import logging.handlers

from mimosa import MIMOSA, load_params

handler = logging.handlers.WatchedFileHandler("mainlog.log")
handler.setFormatter(
    logging.Formatter("[%(levelname)s, %(asctime)s] %(name)s - %(message)s")
)
root = logging.getLogger()
root.setLevel("INFO")
root.addHandler(handler)

params = load_params()

# Make changes to the params if needed
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve(verbose=False) # (1)!
model1.save("run1")
```

1. By setting `verbose=False`, the IPOPT output is not printed.
     If you're doing many runs, this is probably useful. The termination status of IPOPT is
     logged to the log file anyway.