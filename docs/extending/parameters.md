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

The configuration file can be used to set *scalar* parameters. However, some parameters are regional. These are created like:

```python
m.new_regional_param = Param(m.regions)
```

Initializing their value is done in three steps:

1. **Create a CSV file** with a column `region` and the columns with regional parameter values you want to use:

    In the folder [`mimosa/inputdata/regionalparams/`]({{config.repo_url}}/tree/master/mimosa/inputdata/regionalparams/), create a new CSV file:

    ```python hl_lines="10"
    mimosa
    │   ...
    │
    └─── inputdata
        └─── config
            │   config_default.csv
        └─── regionalparams
            │   economics.csv
            |   mac.csv 
            |   newfile.csv
            |   ...

    ```

    This file should have at least a column `region` and one (or more) columns for the regional values:

    :fontawesome-solid-file-csv: `mimosa/inputdata/regionalparams/newfile.csv`

    | region | newparam1 | newparam2 | ... |
    | -- | -- | -- | -- |
    | CAN | 1.992 | 2.317 | ... |
    | USA | 2.035 | 1.745 |
    | ... | ... | ... |

    Note that this file can contain multiple columns (for multiple regional parameters). It is good practice to group the parameter values when the parameters are somehow related with each other.

    -------


2. **Register this regional parameter file** in the configuration file under the key [`regional_parameter_files`](../parameters.md#regional_parameter_files):

    ```yaml title="mimosa/inputdata/config/config_default.yaml" hl_lines="7 8 9"
    ...
    regional_parameter_files:
      ...
      default:
        economics:
          filename: inputdata/regionalparams/economics.csv
          regionstype: IMAGE26
        newparamgroup:
          filename: inputdata/regionalparams/newfile.csv
          regionstype: IMAGE26
        ...
    ```

    ??? info "What if my parameter values have a different regional resolution?"

        Test

    -------
    
3. **Link the `Param`** to the relevant column in the CSV file:

    ```python
    m.new_regional_param = Param(m.regions, doc="regional::newparamgroup.newparam1")
    ```

## Advanced: dynamic parameter settings

## Advanced: complex parameter manipulations with `instantiate_params.py`


## Time and region dependent data