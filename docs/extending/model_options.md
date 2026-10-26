# Model options

Model options let a component change which variables or equations it creates without introducing a
separate selectable submodule. Every component receives `inputs` in its `get_constraints(m, inputs)`
function and reads options through `inputs.config_value`. Defaults are defined once in
`config_default.yaml` and supplied by configuration validation.

Keep an option beside the scientific parameters for the component that uses it. For example,
ACCREU adaptation settings belong in `economics.damages.accreu`, and the sea-level-rise
projection belongs in `sealevelrise`.

## Adding an option

For example, the ACCREU damage module can be constructed with no adaptation, combined adaptation, or
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

The component reads the option while adding its variables and equations:

```python
def get_constraints(m, inputs):
    adaptation = inputs.config_value("economics.damages.accreu.adaptation")

    if adaptation == "sectoral":
        # Add separate adaptation variables and equations for each sector
        ...
```

Users can change the option before creating the model:

```python
params = load_params()
params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"
model = MIMOSA(params)
```

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
