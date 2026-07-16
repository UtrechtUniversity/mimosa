# Selectable modules and model options

Most extensions only need a [plain model component](components.md). The approaches on this page are
useful when the configuration determines which version of a component is added, or which groups of
variables and equations it creates.

## When `ModelContext` is needed

MIMOSA first creates a Pyomo `AbstractModel` and only later fills its parameters with data. A choice
that changes the structure of the abstract model therefore has to be available before the Pyomo
parameters are instantiated. `ModelContext` contains these early choices.

```text
Configuration
    │
    ├── selected modules and module options ──> ModelContext
    │                                               │
    │                                               └──> create_abstract_model()
    │                                                        │
    │                                                        └──> selected components
    │
    └── numerical parameters and input data ────────────────> model instantiation
```

Use a normal Pyomo `Param` for numerical and domain assumptions such as coefficients, years and scale
factors. Use `ModelContext` only when a setting changes which model objects are created. Do not copy
ordinary model parameters into `ModelContext` merely to make them easier to access.

## Adding a selectable version of an existing component

Selectable versions are grouped in component packages such as `damages`, `effortsharing` and
`welfare`. The example below adds a minimal damage specification called `newdamage`.

!!! warning "Create the variables used by the rest of MIMOSA"

    Different versions of the same component must create the model variables expected by later
    calculations. For example, every damage specification must provide `m.damage_costs`. Study the
    existing files in the same component package before adding a new version.

### 1. Implement the new version

Create `mimosa/components/damages/newdamage.py`:

```python title="mimosa/components/damages/newdamage.py"
from mimosa.common import (
    AbstractModel,
    ModelContext,
    RegionalEquation,
    Var,
)


def get_constraints(m: AbstractModel, context: ModelContext):
    """Example damage specification with cubic damage costs."""

    m.damage_costs = Var(m.t, m.regions)

    return [
        RegionalEquation(
            m.damage_costs,
            lambda m, t, r: 0.02 * m.temperature[t] ** 3,
        )
    ]
```

This example does not use `context` itself, but the argument is present because every selectable
component is called in the same way.

### 2. Add the version to the selection dictionary

Each selectable component package has a dictionary that connects configuration values to the
corresponding `get_constraints` functions. In the code this is called a registry. Add the new version
to `mimosa/components/damages/__init__.py`:

```python title="mimosa/components/damages/__init__.py" hl_lines="1 7"
from . import coacch, nodamage, newdamage


DAMAGE_MODULES = {
    "COACCH": coacch.get_constraints,
    "nodamage": nodamage.get_constraints,
    "newdamage": newdamage.get_constraints,
}
```

`create_abstract_model` already reads the selected damage function from `DAMAGE_MODULES`. Do not add a
separate call to `newdamage.get_constraints` in `abstract_model.py`.

### 3. Add the configuration choice

Add the same name to the relevant list in `mimosa/inputdata/config/config_default.yaml`:

```yaml title="mimosa/inputdata/config/config_default.yaml" hl_lines="8"
model structure:
  damage module:
    descr: Damage module to be used
    type: enum
    values:
      - COACCH
      - nodamage
      - newdamage
    default: COACCH
```

The dictionary key and the configuration value must match exactly. Users can then select the new
version as follows:

```python
from mimosa import MIMOSA, load_params

params = load_params()
params["model structure"]["damage module"] = "newdamage"
model = MIMOSA(params)
```

The same pattern is used by the emission-trading, financial-transfer, effort-sharing, welfare and
objective components.

## Reading choices and options from `ModelContext`

`ModelContext` provides three ways to read these settings:

```python
context.module("damage")
context.options("damage")
context.option("damage", "adaptation", default="none")
```

- `module(component)` returns the selected version of a selectable component.
- `options(component)` returns all options for that component.
- `option(component, option, default)` returns one option, or the supplied default if it was not set.

Prefer `context.option(...)` to reading `context.components` directly. This keeps the fallback value
next to the equation or variable that uses the option.

## Giving a plain component model options

A component that is always included does not need an entry in `ModelContext` unless it uses model
options. If it does, add it to the fixed components in `Preprocessor._create_model_context` in
`mimosa/core/initializer.py`:

```python title="mimosa/core/initializer.py" hl_lines="7"
components={
    # ... selectable components ...

    # Fixed/non-registry components
    "emissions": fixed_component("emissions"),
    "sealevelrise": fixed_component("sealevelrise"),
    "mitigation": fixed_component("mitigation"),
    "cobbdouglas": fixed_component("cobbdouglas"),
    "new_component": fixed_component("new_component"),
}
```

The component can then read an option while it creates its model objects:

```python
def get_constraints(m, context):
    include_feedback = context.option(
        "new_component",
        "include feedback",
        default=False,
    )

    if include_feedback:
        # Add the optional variables and equations
        ...
```

Fixed-component options are read from `<component> options` under `model structure`. Selectable
component options are read from `<component> module options`. The configuration entry must be defined
and validated in `config_default.yaml`; see [Adding parameters and data](parameters.md) for the
configuration format.

## Testing selectable components and model options

In addition to the tests recommended for [plain components](components.md#4-test-the-component), test
that:

1. the configuration parser accepts the new name and any options;
2. selecting the new version creates the expected variables and equations;
3. at least one existing version still constructs successfully;
4. each option produces the intended set of model objects; and
5. unsupported names and option values give a clear configuration error.

Model construction with `MIMOSA(params, prerun=False)` is normally sufficient for these tests. Only
behaviour that depends on an optimiser needs a full solver run.
