Parameteres are values used in MIMOSA that can be changed without changing the code. A new parameter called `new_param` can be added in the `get_constraints` function of any component:


```python hl_lines="4"
def get_constraints(m):
    # ... existing code ...
    
    m.new_param = Param()
    
    # ... existing code ...
```

This creates an abstract parameter (without a value). It still needs a value. How to set this depends on the type of parameter. MIMOSA supports three types of parameters:

1. [**Scalar parameters**](#config-params): Scalar parameters (that don't depend on region or time) are defined in the `config_default.yaml` file and can be modified at runtime by modifying the `params` dictionary. These parameters are typically used for model settings, such as the pure rate of time preference (PRTP), discount rates, etc.
2. [**Regional parameters**](#regional-params): Regional parameters (that don't depend on time) are defined in a CSV file and can be linked to the `Param` using the `doc` field. These parameters are typically used for regional coefficients for damage functions, emissions factors, etc.
3. [**Time and region dependent data**](#time-and-region-dependent-data): These parameters depend on both time and region, such as baseline population, baseline GDP, etc. Their data comes from CSV files in IAMC format.

## 1. Parameters from config file: non-regional parameters {id="config-params"}

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

## 2. Regional parameters {id="regional-params"}

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

    ```yaml title="mimosa/inputdata/config/config_default.yaml" hl_lines="8 9 10"
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

        Todo

    -------
    
3. **Link the `Param`** to the relevant column in the CSV file:

    ```python
    m.new_regional_param = Param(m.regions, doc="regional::newparamgroup.newparam1")
    ```

## 3. Time and region dependent data {id="time-and-region-dependent-data"}

The third type of parameters are time and region dependent parameters. This is typically used for baseline data, such as population, GDP, etc. 

They are defined like any other parameter, but with the `time` and `regions` dimensions. For example, the population data is defined as:

```python
m.population = Param(
    m.t,
    m.regions,
    doc="timeandregional::population",
    units=quant.unit("billion people"), # (1)!
)
```

1.  The `units` field is optional, but it is good practice to include it. This is especially important for numerical values with units (values that are not dimensionless). The `quant` module is imported as `quant` from the `mimosa` package.

Just like regional parameters, the parameter values are linked to the underlying data using the `doc` field, starting with `timeandregional::`. The input data source should be in IAMC format. For each parameter, the filename, variable, scenario and model should be specified in the configuration file:

```yaml title="mimosa/inputdata/config/config_default.yaml" hl_lines="8 9 10 11 12"
...
input:
  variables:
    population: # (1)!
      descr: Data source of population
      type: datasource
      default:
        variable: Population
        unit: population_unit
        scenario: "{SSP}-Ref-SPA0-V17"
        model: IMAGE
        file: inputdata/data/data_IMAGE_SSP.csv
    ...
```

1. The name defined here (`population`) should match the name used in the `doc` field of the parameter definition: <code>timeandregional::<b>population</b></code>.

The `file` field should point to the IAMC formatted data file. The IAMC format is a CSV file with the following columns:

:fontawesome-solid-file-csv: [`mimosa/inputdata/data/data_IMAGE_SSP.csv`]({{config.repo_url}}/tree/master/mimosa/inputdata/data/data_IMAGE_SSP.csv)

{{ read_csv("mimosa/inputdata/data/data_IMAGE_SSP.csv", nrows=3) }}
|... | ... |... |... |

???+ info "Configuration values dependent on other parameter values"

    In the example above, the name of the scenario depends on the [`SSP`](../parameters.md#SSP). Every string in the configuration file can contain references
    to other parameters, and are referred to using curly brackets `{}`. If you want to refer to a nested parameter (like [`effort sharing > regime`](../parameters.md#effort%20sharing.regime)), they should be joined
    with ` - `:

    ```yaml
    scenario: "Scenario-with-{SSP}-and-{effort sharing - regime}"
    ```

## 4. Advanced: dynamic parameter settings

## 5. Advanced: complex parameter manipulations with `instantiate_params.py`

