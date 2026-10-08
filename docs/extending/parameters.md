# Adding parameters and data

Parameters are values used in MIMOSA that can be changed without changing the code.

`Param` imported from `mimosa.common` is a factory that returns a standard Pyomo parameter.
Ordinary Pyomo arguments, including `initialize`, `default`, `units` and `mutable`, work as usual.
For component filtering or type checks, import `PyomoParam` from `mimosa.common` instead.

The factory also accepts already resolved input values with source metadata:

```python
from mimosa.common import ConcreteModel, Param, SourcedValue

m = ConcreteModel()
m.alpha = Param(
    initialize=SourcedValue(0.3, "::economics.GDP.alpha"),
)
# m.alpha is a Pyomo parameter; m.alpha.doc is "::economics.GDP.alpha".
```

`SourcedValue` does not load or convert data. It carries values and a documentation key using the
existing `::config.path`, `regional::category.name` or `timeandregional::variable` conventions.
Omit `doc` when using a sourced initializer: supplying both raises `ValueError`.
The concrete builder uses explicit initialization. `doc` is documentation metadata and does not
load or override values. A doc-only declaration such as `Param(doc="::economics.PRTP")` does
not initialize the parameter; use `initialize=inputs.config("economics.PRTP")` instead.

## Explicit input lookup

`ModelInputs` is available from `mimosa.core.model_inputs` for independent construction code.
It consumes validated configuration with references resolved, its parser tree, and the existing
`DataStore` and `RegionalParamStore`. For example:

```python
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.core.model_inputs import ModelInputs

params, parser_tree = check_params({}, return_parser_tree=True)
params = parse_param_values(params)
inputs = ModelInputs(
    params=params,
    parser_tree=parser_tree,
    data_store=DataStore(params),
    regional_store=RegionalParamStore(params, parser_tree),
)
```

Once the model's sets are defined, parameters can use a single source reference:

```python
m.alpha = Param(initialize=inputs.config("economics.GDP.alpha"))
m.init_capitalstock_factor = Param(
    m.regions,
    initialize=inputs.regional("economics", "init_capital_factor"),
)
m.population = Param(
    m.t, m.regions,
    initialize=inputs.time_regional("population"),
    units=quant.unit("billion people"),
)
```

These methods return `SourcedValue` objects. Scalar quantities are converted using their configured
units; regional data retains existing mapping and per-region overrides; time-dependent data is
interpolated using the existing store. Keys are timestep indices and region names, not calendar years.
`inputs.t`, `inputs.regions`, `inputs.time_grid` and `inputs.year(t)` expose the configured indices
and calendar grid. Input lookup itself does not apply component-specific consistency checks.

For Python decisions, use `inputs.config_value("model structure.damage module")` or retrieve a whole
section, such as `inputs.config_value("model structure.damage module options")`. Scalar quantity
lookups return converted magnitudes, while whole sections retain their parsed contents without
recursive quantity conversion. Lookups do not modify the configuration.

`inputs.time_config(path)` linearly interpolates a non-empty configuration mapping of ascending
calendar years to numeric values onto the model time grid. Values outside the keyframe range use
the nearest endpoint. It returns timestep-indexed values with the original config path as metadata.
The caller chooses the source; for example, mitigation can select its SSP calibration explicitly:

```python
ssp = inputs.config_value("SSP")
m.MAC_SSP_calibration_factor = Param(
    m.t,
    initialize=inputs.time_config(f"economics.MAC.SSP_calibration_factor.{ssp}"),
    units=quant.unit("dimensionless"),
)
```

Configure inputs before preparing the stores and lookup object.

The component interface is `get_constraints(m: ConcreteModel, inputs: ModelInputs)`.
Every component receives prepared input lookup directly. For example, the default
`welfare_loss_minimising` component initializes:

```python
m.elasmu = Param(initialize=inputs.config("economics.elasmu"))
```

Its `param::elasmu` documentation marker continues to work because the factory preserves the source
key in `doc`. The Cobb–Douglas component now also uses explicit lookup for its capital-stock
coefficient, production parameters and damage-ignore flag. For example:

```python
m.alpha = Param(initialize=inputs.config("economics.GDP.alpha"))
m.init_capitalstock_factor = Param(
    m.regions,
    initialize=inputs.regional("economics", "init_capital_factor"),
    units=quant.unit("dimensionless"),
)
```

Emissions and mitigation also use explicit lookup; mitigation chooses its regional calibration
column and SSP keyframe path locally. Sea-level rise reads its projection through `config_value`.
COACCH also chooses its combined/separate, adaptation and quantile sources locally. Its
declarations can select either a sourced value or a constant without a separate `doc` argument:

```python
m.damage_noslr_a = Param(
    m.regions,
    initialize=1 if combined else inputs.regional("COACCH", f"NoSLR_a (q={quantile})"),
)
```

Only the selected branch performs a lookup. A plain constant initializes every regional entry
and has no source metadata; sourced regional values carry the selected column name. This replaces
the former combined-damage backend override while retaining the existing parameter declarations.

ACCREU and ACCREU_CGE also initialize configured and regional parameters explicitly.
ACCREU passes `inputs` to its existing sector helpers; adaptation options are read and validated
once by `get_adaptation_options(inputs)`. Its sector calibration objects and equation helpers
are retained. Component options use `config_value`, and ACCREU_CGE selects quantile columns
using its existing two-decimal naming convention.

All component configuration/data parameters now use explicit initialization, including the
remaining welfare variants, objectives, effort-sharing settings and cost-pool payment limits.
Derived parameters retain their existing rules. The mutable no-policy damage parameter is
filled later by the baseline hook. Shared base sets and input parameters are initialized before
components run, so `m.t`, `m.regions` and previously declared values are immediately available.
Declare dependencies before any initializer or bound that reads them. Equation lambdas should
still use the model passed to them, so the same equations work in simulation and optimization.

For checks that need initialized model values, a standard Pyomo `validate` callback can keep
validation with the parameter declaration. Emissions uses this for its pulse:

```python
def _validate_emissions_pulse(m, pulse_amount):
    pulse_year = value(m.emissions_pulse_year)
    if pulse_amount != 0 and pulse_year not in {m.year(t) for t in m.t}:
        raise ValueError(
            f"Emissions pulse year {pulse_year} is not on the model time grid."
        )
    return True

m.emissions_pulse_year = Param(initialize=inputs.config("emissions.pulse.year"))
m.emissions_pulse_amount = Param(
    initialize=inputs.config("emissions.pulse.amount"),
    validate=_validate_emissions_pulse,
)
```

Pyomo calls this function when assigning a parameter value: during `create_instance` for an
abstract model, or when adding the parameter to a concrete model. Dependencies such as the
pulse year and time grid must be declared first. The callback returns `True` for valid values
or raises an explanatory error. It adds no solver constraint.

Component helpers can use ordinary imports for type hints and editor completion:

```python
from mimosa.core.model_inputs import ModelInputs

def _get_emissions_constraints(m: ConcreteModel, inputs: ModelInputs):
    # ...
    pass
```

## Adding a parameter

A new parameter called `new_param` can be added in the `get_constraints` function of any component:

```python hl_lines="4"
def get_constraints(m, inputs):
    # ... existing code ...
    
    m.new_param = Param(initialize=3.0)
    
    # ... existing code ...
```

This creates an initialized constant. For configurable inputs, MIMOSA supports three types of parameters:

1. [**Scalar parameters**](#config-params): Scalar parameters (that don't depend on region or time) are defined in the `config_default.yaml` file and can be modified at runtime by modifying the `params` dictionary. These parameters are typically used for model settings, such as the pure rate of time preference (PRTP), discount rates, etc.
2. [**Regional parameters**](#regional-params): Regional parameters (that don't depend on time) are defined in a CSV file and initialized through `inputs.regional`. These parameters are typically used for regional coefficients for damage functions, emissions factors, etc.
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

Initialize the parameter from its configuration entry, using prepared input lookup:

```python
m.PRTP = Param(initialize=inputs.config("economics.PRTP"))
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
m.new_regional_param = Param(
    m.regions, initialize=inputs.regional("newparamgroup", "newparam1")
)
```

Initializing their value is done in three steps:

1. **Create a CSV file** with a column `region` and the columns with regional parameter values you want to use:

    In the folder [`mimosa/inputdata/regionalparams/`]({{config.repo_url}}/tree/master/mimosa/inputdata/regionalparams/), create a new CSV file:

    ```text
    mimosa
    │   ...
    │
    └─── inputdata
        └─── config
            │   config_default.yaml
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

    ```yaml title="mimosa/inputdata/config/config_default.yaml"
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

        Give every regional parameter file a `regionstype` describing the regions in its `region`
        column. If this differs from the model's selected [`regionstype`](../parameters.md#regionstype),
        MIMOSA looks for a conversion table registered under
        [`regionsmappings`](../parameters.md#regionsmappings):

        ```yaml title="mimosa/inputdata/config/config_default.yaml"
        regionsmappings:
          default:
            - regionstype1: IMAGE26
              regionstype2: NEW_REGIONS
              conversiontable: inputdata/regions/IMAGE26_NEW_REGIONS.csv
        ```

        The conversion CSV must contain columns named `IMAGE26` and `NEW_REGIONS`, with each row
        connecting regions in the two definitions. The mapping is applied by
        [`region_mappers.py`]({{config.repo_url}}/blob/master/mimosa/common/regional_params/region_mappers.py).
        When several source regions map to one target region, numeric parameter values are averaged
        and non-numeric values use the first value. The same table can also be used in the reverse
        direction.

        This mechanism only converts regional parameter files. It does not aggregate or disaggregate
        model variables, outputs or time-dependent input data. A new model region definition must
        also be added to the allowed `regionstype` values, its region codes must be listed under
        `regions`, and time-dependent input data must be available at that resolution.

    -------
    
3. **Link the `Param`** to the relevant column in the CSV file:

    ```python
    m.new_regional_param = Param(
        m.regions, initialize=inputs.regional("newparamgroup", "newparam1")
    )
    ```

## 3. Time and region dependent data {id="time-and-region-dependent-data"}

The third type of parameters are time and region dependent parameters. This is typically used for baseline data, such as population, GDP, etc. 

They are defined like any other parameter, but with the `time` and `regions` dimensions. For example, the population data is defined as:

```python
m.population = Param(
    m.t,
    m.regions,
    initialize=inputs.time_regional("population"),
    units=quant.unit("billion people"), # (1)!
)
```

1.  The `units` field is optional, but it is good practice to include it. This is especially important for numerical values with units (values that are not dimensionless). Import `quant` from `mimosa.common`. See [Units](units.md) for the standard model units and conversion behaviour.

The lookup selects and interpolates the configured IAMC data source and supplies its documentation
metadata automatically. For each input, specify the filename, variable, scenario and model in the
configuration file:

```yaml title="mimosa/inputdata/config/config_default.yaml"
...
input:
  variables:
    population: # (1)!
      descr: Data source of population
      type: datasource
      default:
        variable: Population
        unit: population_unit
        scenario: "{SSP}-Baseline"
        model: IMAGE 3.4
        file: inputdata/data/data_IMAGE_SSP_updated.csv
    ...
```

1. The name defined here (`population`) must match the argument to `inputs.time_regional("population")`.

The `file` field should point to the IAMC formatted data file. The IAMC format is a CSV file with the following columns:

:fontawesome-solid-file-csv: [`mimosa/inputdata/data/data_IMAGE_SSP_updated.csv`]({{config.repo_url}}/tree/master/mimosa/inputdata/data/data_IMAGE_SSP_updated.csv)

{{ read_csv("mimosa/inputdata/data/data_IMAGE_SSP_updated.csv", nrows=3) }}
|... | ... |... |... |

???+ info "Configuration values dependent on other parameter values"

    In the example above, the name of the scenario depends on the [`SSP`](../parameters.md#SSP). Every string in the configuration file can contain references
    to other parameters, and are referred to using curly brackets `{}`. If you want to refer to a nested parameter (like [`model structure > effortsharing module`](../parameters.md#model structure.effortsharing module)), they should be joined
    with ` - `:

    ```yaml
    scenario: "Scenario-with-{SSP}-and-{model structure - effortsharing module}"
    ```
