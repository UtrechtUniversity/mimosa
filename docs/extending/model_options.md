# Model options

Model options let a component change which variables or equations it creates without introducing a
separate selectable submodule. Every component receives `inputs` in its `get_constraints(m, inputs)`
function and reads options through `inputs.config_value`. Defaults are defined once in
`config_default.yaml` and supplied by configuration validation.

There are two naming conventions:

| Component type                    | Configuration group under `model structure` | Example                 |
| --------------------------------- | ------------------------------------------- | ----------------------- |
| Selectable component              | `<name> module options`                     | `damage module options` |
| Component that is always included | `<name> options`                            | `emissions options`     |

The component catalogue determines which naming convention is used:

```python title="mimosa/model_builder.py"
MODEL_COMPONENTS = (
    fixed_component("emissions", emissions.get_constraints),
    selectable_component("damage", damages.DAMAGE_MODULES),
    # ... remaining components ...
)
```

`selectable_component` reads `<name> module` to select a function. The function reads its own
options from the configuration path shown above; no separate options object is created.

## Options for a selectable component

Suppose the selected damage module can be constructed with no adaptation, combined adaptation, or
separate adaptation by sector. Define the option under `damage module options` in
`config_default.yaml`:

```yaml title="mimosa/inputdata/config/config_default.yaml"
model structure:
  # ... damage module and other choices ...

  damage module options:
    adaptation:
      descr: How adaptation is represented in the selected damage module
      type: enum
      values:
        - none
        - combined
        - separate
      default: combined
```

Defining each named option as a normal configuration entry gives it type checking, a default value and
an entry in the generated parameter reference.

The selected damage submodule can read it while adding its variables and equations:

```python
def get_constraints(m, inputs):
    adaptation = inputs.config_value("model structure.damage module options.adaptation")

    if adaptation == "separate":
        # Add separate adaptation variables and equations for each sector
        ...
```

Users can change the option before creating the model:

```python
params = load_params()
params["model structure"]["damage module options"]["adaptation"] = "separate"
model = MIMOSA(params)
```

All submodules receive the same prepared input lookup. Each reads the configuration values
relevant to its calculations.

## Options for a component that is always included

For a fixed component, omit the word `module`. The following example adds an illustrative option to
the emissions component:

```yaml title="mimosa/inputdata/config/config_default.yaml"
model structure:
  # ... module choices and other options ...

  emissions options:
    include feedback:
      descr: Include the additional emissions feedback equations
      type: bool
      default: false
```

The emissions component can read it with:

```python
def get_constraints(m, inputs):
    include_feedback = inputs.config_value("model structure.emissions options.include feedback")

    if include_feedback:
        # Add the additional variables and equations
        ...
```

Users change it through the corresponding configuration group:

```python
params["model structure"]["emissions options"]["include feedback"] = True
```

## Options for a new component

Register the component in the catalogue as before:

```python title="mimosa/model_builder.py"
fixed_component("new_component", new_component.get_constraints),
```

Define `new_component options` under `model structure` and read the value at its full path:

```python
include_feedback = inputs.config_value("model structure.new_component options.include feedback")
```

For a selectable component, use `new_component module options` instead. Adding options does
not require a second registration or a configuration object.

## Reading a whole section

When several related settings are needed together, a plain dictionary can keep the code clear:

```python
options = inputs.config_value("model structure.damage module options")
adaptation = options["ACCREU_adaptation"]
determination = options["ACCREU_adaptation_determination"]
```

Read a module selection with `inputs.config_value("model structure.damage module")`.
The configuration parser supplies defaults and validates supported values before construction.
`config_value` returns Python values for decisions; use `inputs.config(...)` when creating a
Pyomo parameter with source metadata. See [Adding parameters and data](parameters.md).

## Model option or Pyomo parameter?

Use a model option when the value changes which model objects are created. For example, an option can
enable a sector or choose between a combined and sector-specific set of adaptation equations.

Use a Pyomo `Param` for a numerical or domain assumption within equations, such as an adaptation cost,
effectiveness coefficient or start year. Parameters receive values when declared on the concrete
model through explicit initialization. See [Adding parameters and data](parameters.md).

## Testing model options

At minimum, test that:

1. the configuration parser accepts every documented option value;
2. each option produces the intended variables and equations;
3. the documented default produces the normal model structure; and
4. unsupported option values give a clear configuration error.

Model construction with `MIMOSA(params, prerun=False)` is normally sufficient. Only behaviour that
depends on an optimiser needs a full solver run.
