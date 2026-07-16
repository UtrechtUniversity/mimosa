# Model options

Model options let a component change which variables or equations it creates without introducing a
separate selectable submodule. Every component receives `context` in its `get_constraints(m, context)`
function and can use it to read these options.

There are two naming conventions:

| Component type                    | Configuration group under `model structure` | Example                 |
| --------------------------------- | ------------------------------------------- | ----------------------- |
| Selectable component              | `<name> module options`                     | `damage module options` |
| Component that is always included | `<name> options`                            | `emissions options`     |

The component catalogue determines which naming convention is used:

```python title="mimosa/abstract_model.py"
MODEL_COMPONENTS = (
    fixed_component("emissions", emissions.get_constraints),
    selectable_component("damage", damages.DAMAGE_MODULES),
    # ... remaining components ...
)
```

`fixed_component` reads `<name> options`. `selectable_component` reads both `<name> module` and
`<name> module options`.

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
def get_constraints(m, context):
    adaptation = context.option(
        "damage",
        "adaptation",
        default="combined",
    )

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

All submodules in a selectable package receive the same options dictionary. Each submodule may use the
options that are relevant to its calculations.

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
def get_constraints(m, context):
    include_feedback = context.option(
        "emissions",
        "include feedback",
        default=False,
    )

    if include_feedback:
        # Add the additional variables and equations
        ...
```

Users change it through the corresponding configuration group:

```python
params["model structure"]["emissions options"]["include feedback"] = True
```

The existing fixed components—`emissions`, `sealevelrise`, `mitigation` and `cobbdouglas`—are already
available through `ModelContext`.

## Options for a new fixed component

A plain component is already registered with `fixed_component` in the component catalogue. That entry
also makes its options available through `ModelContext`, so no extra Python registration is needed:

```python title="mimosa/abstract_model.py"
fixed_component("new_component", new_component.get_constraints),
```

Define `new_component options` under `model structure` and read individual values with
`context.option("new_component", "option name", default=...)`.

## Other ways to read options

`ModelContext` provides three related methods:

```python
context.module("damage")
context.options("damage")
context.option("damage", "adaptation", default="combined")
```

- `module(component)` returns the selected submodule name for a selectable component.
- `options(component)` returns the complete options dictionary.
- `option(component, option, default)` returns one option, or the supplied default if it was not set.

Prefer `context.option(...)` when a component only needs one setting. It keeps the fallback value next
to the variables or equations affected by that option.

## Model option or Pyomo parameter?

Use a model option when the value changes which model objects are created. For example, an option can
enable a sector or choose between a combined and sector-specific set of adaptation equations.

Use a Pyomo `Param` for a numerical or domain assumption within equations, such as an adaptation cost,
effectiveness coefficient or start year. Pyomo parameters receive their values later, when the
abstract model is instantiated. See [Adding parameters and data](parameters.md) for these values.

## Testing model options

At minimum, test that:

1. the configuration parser accepts every documented option value;
2. each option produces the intended variables and equations;
3. the documented default produces the normal model structure; and
4. unsupported option values give a clear configuration error.

Model construction with `MIMOSA(params, prerun=False)` is normally sufficient. Only behaviour that
depends on an optimiser needs a full solver run.
