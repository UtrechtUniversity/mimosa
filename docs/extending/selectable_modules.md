# Selectable modules

A selectable module lets users choose between different representations of one part of MIMOSA. The
selected name is stored under `model structure` in the configuration. MIMOSA uses that name to choose
the corresponding `get_constraints` function.

This page covers two common changes:

1. adding a submodule to an existing selection, such as another damage function;
2. adding a new model part with its own set of submodules, such as alternative biodiversity or health
   representations.

## Adding a submodule to an existing selection

Selectable submodules are grouped in packages such as `damages`, `effortsharing` and `welfare`. The
example below adds a damage specification called `newdamage`.

!!! warning "Create the variables used by the rest of MIMOSA"

    Submodules within the same selection must create the model variables expected by later
    calculations. For example, every damage specification must provide `m.damage_costs`. Study the
    existing files in the same package before adding a new one.

### 1. Implement the new submodule

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

This example does not use `context` itself, but the argument is present because every component is
called in the same way.

### 2. Add it to the selection dictionary

Each selectable package has a dictionary connecting configuration values to `get_constraints`
functions. In the code this dictionary is called a registry. Add the new submodule to
`mimosa/components/damages/__init__.py`:

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

Add the same name to the existing list in `mimosa/inputdata/config/config_default.yaml`:

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

The dictionary key and configuration value must match exactly. Users can then select it with:

```python
from mimosa import MIMOSA, load_params

params = load_params()
params["model structure"]["damage module"] = "newdamage"
model = MIMOSA(params)
```

The same pattern is used by the emission-trading, financial-transfer, effort-sharing, welfare and
objective components.

## Adding a new set of selectable submodules

Sometimes the new model part does not belong to an existing selection. For example, a modeller might
want MIMOSA to support several biodiversity representations: no biodiversity impacts, a simple
temperature-dependent representation, and a more detailed representation based on ecosystems.

This requires a new component package, a new selection dictionary, a configuration choice, and one
entry in MIMOSA's component catalogue.

### 1. Create the package and submodules

Create one file for each biodiversity representation:

```text
mimosa/components/biodiversity/
├── __init__.py
├── no_biodiversity.py
├── temperature_dependent.py
└── ecosystems.py
```

Each file contains a `get_constraints(m, context)` function. All three should create the same main
output variables, so other components can use them without knowing which representation was selected.
For example, they could all define `m.biodiversity_loss`, while calculating it in different ways.

### 2. Create the selection dictionary

Connect the user-facing names to those functions in `mimosa/components/biodiversity/__init__.py`:

```python title="mimosa/components/biodiversity/__init__.py"
from . import ecosystems, no_biodiversity, temperature_dependent


BIODIVERSITY_MODULES = {
    "none": no_biodiversity.get_constraints,
    "temperature_dependent": temperature_dependent.get_constraints,
    "ecosystems": ecosystems.get_constraints,
}
```

### 3. Define the configuration choice

Add a new enum under `model structure`:

```yaml title="mimosa/inputdata/config/config_default.yaml"
model structure:
  # ... existing module choices ...

  biodiversity module:
    descr: Biodiversity representation to be used
    type: enum
    values:
      - none
      - temperature_dependent
      - ecosystems
    default: none
```

### 4. Add the selection to the component catalogue

Import the package and add it to `MODEL_COMPONENTS` in
`mimosa/abstract_model.py`:

```python title="mimosa/abstract_model.py"
from mimosa.components import biodiversity


MODEL_COMPONENTS = (
    # ... existing components ...
    selectable_component("biodiversity", biodiversity.BIODIVERSITY_MODULES),
)
```

The name `biodiversity` must match the first part of `biodiversity module` in the configuration.
MIMOSA then reads the selection into `ModelContext` and calls the chosen function automatically.
Place the entry near the model components that use or produce related quantities.

Users can now select a representation in the same way as existing modules:

```python
params["model structure"]["biodiversity module"] = "ecosystems"
```

If the submodules also need settings that do not justify separate representations, add
[model options](model_options.md).

## Testing selectable modules

In addition to the tests recommended for [plain components](components.md#4-test-the-component), test
that:

1. the configuration parser accepts every listed submodule name;
2. each selection creates the variables expected by the rest of MIMOSA;
3. `MIMOSA(params, prerun=False)` can construct every submodule; and
4. an unsupported name gives a clear configuration error.

Only behaviour that depends on an optimiser needs a full solver run.
