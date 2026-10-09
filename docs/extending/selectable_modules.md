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
    ConcreteModel,
    RegionalEquation,
    Var,
)

from mimosa.core.model_inputs import ModelInputs


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Example damage specification with cubic damage costs."""

    m.damage_costs = Var(m.t, m.regions)

    return [
        RegionalEquation(
            m.damage_costs,
            lambda m, t, r: 0.02 * m.temperature[t] ** 3,
        )
    ]
```

This example does not use `inputs` itself, but the argument is present because every component is
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

The package's `get_constraints(m, inputs)` reads the selected damage function from `DAMAGE_MODULES`.
The model builder calls that package function. Do not add a
separate call to `newdamage.get_constraints` in `model_builder.py`.

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
call in MIMOSA's model builder.

### 1. Create the package and submodules

Create one file for each biodiversity representation:

```text
mimosa/components/biodiversity/
├── __init__.py
├── no_biodiversity.py
├── temperature_dependent.py
└── ecosystems.py
```

Each file contains a `get_constraints(m, inputs)` function. All three should create the same main
output variables, so other components can use them without knowing which representation was selected.
For example, they could all define `m.biodiversity_loss`, while calculating it in different ways.

### 2. Create the selection dictionary and package entry point

Connect the user-facing names to those functions in `mimosa/components/biodiversity/__init__.py`:

```python title="mimosa/components/biodiversity/__init__.py"
from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import ecosystems, no_biodiversity, temperature_dependent


BIODIVERSITY_MODULES = {
    "none": no_biodiversity.get_constraints,
    "temperature_dependent": temperature_dependent.get_constraints,
    "ecosystems": ecosystems.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    module = inputs.config_value("model structure.biodiversity module")
    get_module_constraints = load_from_registry(module, BIODIVERSITY_MODULES)
    return get_module_constraints(m, inputs)
```

The package owns its selection. `load_from_registry` reports an unsupported name together with
the available choices. The chosen submodule still receives the same model and inputs.

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

### 4. Call the package in the model builder

Import the package and call its `get_constraints` function in `create_model` in
`mimosa/model_builder.py`:

```python title="mimosa/model_builder.py"
from mimosa.components import biodiversity


def create_model(inputs: ModelInputs):
    m = create_base_model(inputs)
    constraints = []
    # ... existing component calls ...
    constraints.extend(biodiversity.get_constraints(m, inputs))
    # ... remaining components and constraint attachment ...
```

The package reads `model structure.biodiversity module` from `ModelInputs` and calls the chosen
function. Place the construction call near the model components that use or produce related quantities.

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
