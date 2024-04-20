Parameteres are values used in MIMOSA that can be changed without changing the code. A new parameter called `new_param` can be added in the `get_constraints` function of any component:


```python hl_lines="4"
def get_constraints(m):
    # ... existing code ...
    
    m.new_param = Param()
    
    # ... existing code ...
```

This creates an abstract parameter (without a value). It still needs a value. This can be done for [scalars (non-regional parameters)](#config-params) using the default configuration file and for [regional parameters](#regional-params) using CSV input values.

## Parameters from config file: non-regional parameters {id="config-params"}

All parameters that are not regional have an entry in the `config_default.yaml` file (located in the folder [`mimosa/inputdata/config/`]({{config.repo_url}}/tree/master/mimosa/inputdata/config/config_default.yaml)). This defines the type of the parameter (numerical, boolean, string, etc.), the default value, and the range of possible values. For example, the following entry defines the parameter [`economics - PRTP`](../parameters.md#economics.PRTP):

```yaml title="mimosa/inputdata/config/config_default.yaml"
...
economics:
  PRTP:
    descr: Pure rate of time preference
    type: float
    min: 0
    max: 0.2
    default: 0.015
...
```

Each parameter entry in the configuration file contains the following fields:

* `descr`: A description of the parameter
* `type`: The type of the parameter (e.g. [`float`](#parser-float), [`int`](#parser-int), [`str`](#parser-str), [`bool`](#parser-bool), ...)
* `default`: The default value of the parameter
* Optionally some extra fields depending on the type of parameter

The next step is to link this configuration entry to the `Param` in MIMOSA. This is done using the `doc` field when defining the `Param`:

```python
m.PRTP = Param(doc="::economics.PRTP")
```

Note that the `config_default.yaml` file is structured as a nested dictionary. In this case, the PRTP parameter is located within the `economics` group. This structure can be arbitrary and doesn't need to match the name of the component. It is purely used to structure the configuration file.

When running MIMOSA, the command `params = load_params()` loads all the default values from the configuration file as a nested dictionary. These values can be changed by modifying the `params` dictionary:

```python hl_lines="3 4"
from mimosa import MIMOSA, load_params

params = load_params() 
params["economics"]["PRTP"] = 0.001
...
```

After this step, MIMOSA always double checks the dictionary `params` to check if all the parameter values have the correct type and match specifications of the configuration entry (for example, if the value is within the specified range). If not, MIMOSA will raise an error.


#### Types of parameter values

In the example above, the PRTP has a type [`float`](#parser-float). The following types are supported (especially note that for numerical values with units (values that are not dimensionless), the type [`quantity`](#parser-quantity) should be used):

{parsers::types}

## Regional parameters {id="regional-params"}

## Advanced: dynamic parameter settings

## Advanced: complex parameter manipulations with `instantiate_params.py`


## Time and region dependent data