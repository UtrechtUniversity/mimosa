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
The default parameters from `load_params()` are given as a nested dictionary. Every item of this dictionary can be changed. Note that only the values can be changed, it is not possible to add or substract parameters to this dictionary (without [Extending MIMOSA](extending_mimosa.md)).

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
model1.solve(verbose=False)
model1.save("run1")
```