# Running MIMOSA

### Base run
A basic run of MIMOSA requires 4 steps: loading the parameters, building the model instance, solving the model and finally saving the output.
With this code, the default parameter values are used (see [Parameter reference](../parameters.md)).

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

