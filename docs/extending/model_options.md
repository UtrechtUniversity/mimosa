# Model options

Model options let a component change which variables or equations it creates without introducing a
separate selectable submodule. Every component receives `inputs` in its `get_constraints(m, inputs)`
function and reads options through `inputs.config_value`. Defaults are defined once in
`config_default.yaml` and supplied by configuration validation.

Keep an option beside the scientific parameters for the component that uses it. For example,
ACCREU adaptation settings belong in `economics.damages.accreu`, and the sea-level-rise
projection belongs in `sealevelrise`. The `model structure` section only selects implementations.
An option's location does not depend on whether a component is fixed or selectable.

## Options for a selectable component

Suppose the selected damage module can be constructed with no adaptation, combined adaptation, or
separate adaptation by sector. Define the option under `economics > damages > accreu` in
`config_default.yaml`:

```yaml title="mimosa/inputdata/config/config_default.yaml"
economics:
  damages:
    accreu:
      adaptation:
        descr: How adaptation is represented in ACCREU
        type: enum
        values:
          - noadaptation
          - combined
          - separate
        default: separate
```

Defining each named option as a normal configuration entry gives it type checking, a default value and
an entry in the generated parameter reference.

The selected damage submodule can read it while adding its variables and equations:

```python
def get_constraints(m, inputs):
    adaptation = inputs.config_value("economics.damages.accreu.adaptation")

    if adaptation == "separate":
        # Add separate adaptation variables and equations for each sector
        ...
```

Users can change the option before creating the model:

```python
params = load_params()
params["economics"]["damages"]["accreu"]["adaptation"] = "separate"
model = MIMOSA(params)
```

All submodules receive the same prepared input lookup. Each reads the configuration values
relevant to its calculations.

## Options for a component that is always included

The same approach applies to a component that is always included. The following illustrative
option belongs in the emissions section:

```yaml title="mimosa/inputdata/config/config_default.yaml"
emissions:
    include feedback:
      descr: Include the additional emissions feedback equations
      type: bool
      default: false
```

The emissions component can read it with:

```python
def get_constraints(m, inputs):
    include_feedback = inputs.config_value("emissions.include feedback")

    if include_feedback:
        # Add the additional variables and equations
        ...
```

Users change it through the corresponding configuration group:

```python
params["emissions"]["include feedback"] = True
```

## Options for a new component

Call the component in `create_model` as before:

```python title="mimosa/model_builder.py"
constraints.extend(new_component.get_constraints(m, inputs))
```

Define the setting in the section for that component and read its full path:

```python
include_feedback = inputs.config_value("new_component.include feedback")
```

Use the same approach for selectable components. Adding options does not require a second
registration or a configuration object.

## Reading a whole section

When several related settings are needed together, a plain dictionary can keep the code clear:

```python
options = inputs.config_value("economics.damages.accreu")
adaptation = options["adaptation"]
determination = options["adaptation_determination"]
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
