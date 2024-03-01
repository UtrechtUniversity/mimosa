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

#### Example 2: 

### Doing multiple runs