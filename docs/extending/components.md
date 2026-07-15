# Creating model components

Create a new component when an extension adds a coherent part of the model with its own variables,
parameters and equations. If the change only adds one or two equations to an existing subject area,
it is usually clearer to add them to the existing component instead.

There are two ways to add a component:

| Type of extension | Use when | Example in MIMOSA |
| --- | --- | --- |
| **Fixed component** | The component is always part of the model | Emissions, mitigation or sea-level rise |
| **Selectable module** | The component is one possible implementation of a model part | COACCH versus `nodamage`, or the different effort-sharing regimes |

Both types use the same component interface. They differ only in how they are connected to the model.

## How components enter the model

```text
Configuration
    │
    ├── module choices and options ──> ModelContext
    │
    └── parameter and input values ──> data stores
                                         │
ModelContext ──> create_abstract_model() │
                       │                 │
                       ├── component.get_constraints(model, context)
                       │       ├── adds Params and Vars to the AbstractModel
                       │       └── returns equations and constraints
                       │
                       └── AbstractModel ──> instantiation with data
                                                │
                                                ├── Pyomo optimisation
                                                └── equation-based simulation
```

The distinction between `ModelContext` and Pyomo parameters is important:

* Use a Pyomo `Param` for numerical and domain assumptions, such as a coefficient, year or damage
  scale. These values are added when the abstract model is instantiated. See
  [Adding parameters and data](parameters.md).
* Use `ModelContext` for structural decisions that must be known while the abstract model is being
  constructed, such as which damage module to load or whether a component should create an optional
  group of equations.

Do not copy ordinary model parameters into `ModelContext` merely to make them easier to access.

## The component interface

A component exposes a function called `get_constraints`:

```python title="mimosa/components/new_component.py"
from mimosa.common import (
    AbstractModel,
    GlobalEquation,
    ModelContext,
    Var,
)


def get_constraints(m: AbstractModel, context: ModelContext):
    """Calculate the square of global temperature for every time step."""

    m.temperature_squared = Var(m.t)

    return [
        GlobalEquation(
            m.temperature_squared,
            lambda m, t: m.temperature[t] ** 2,
        )
    ]
```

The function has three responsibilities:

1. Add the component's Pyomo `Param`, `Var` and related objects to the shared `AbstractModel` `m`.
2. Create the equations and constraints that define those variables.
3. Return all those equations and constraints to `create_abstract_model`.

`GlobalEquation` and `RegionalEquation` are used in both the Pyomo model and simulation mode. A direct
Pyomo constraint, or a MIMOSA constraint wrapper such as `GlobalConstraint`, only affects the Pyomo
model. See [Variables, equations and constraints](variables_constraints.md) before deciding which form
to use.

!!! warning "Component order matters"

    A component may only refer to model objects created before it. In the example above,
    `m.temperature` must already exist, so the new component has to be added after the emissions and
    temperature component. Keep related equations together and place a component as early as its
    dependencies allow.

## Adding a fixed component

Use a fixed component if its equations should be present in every MIMOSA model.

### 1. Create the component file

Add the file to `mimosa/components`:

```text
mimosa/
├── abstract_model.py
└── components/
    ├── emissions.py
    ├── mitigation.py
    ├── new_component.py
    └── ...
```

Implement `get_constraints(m, context)` as shown above. Variables and constraint names must be unique
within the shared model.

### 2. Add the component to the model context

Register the fixed component in `Preprocessor._create_model_context` in `mimosa/core/initializer.py`:

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

This gives the component a stable context entry. If no options are configured,
`context.options("new_component")` returns an empty dictionary.

### 3. Call the component during abstract-model construction

Import and call it in `mimosa/abstract_model.py`. Choose its location according to its dependencies:

```python title="mimosa/abstract_model.py" hl_lines="5 13"
from mimosa.components import (
    emissions,
    new_component,
    # ...
)


def create_abstract_model(context: ModelContext):
    m = AbstractModel()
    constraints = []

    constraints.extend(emissions.get_constraints(m, context))

    # m.temperature is available after the emissions component
    constraints.extend(new_component.get_constraints(m, context))

    # ... remaining components ...
```

Do not add a selectable implementation here directly; selectable implementations are loaded through a
registry, as described below.

## Adding an implementation to a selectable module

Use this route when users should choose between alternative implementations. The example below adds a
minimal damage module called `newdamage`.

!!! warning "Preserve the module contract"

    Alternative implementations must create the variables expected by later components. For example,
    every damage implementation must provide `m.damage_costs`. Study the existing implementations in
    the same module package before adding a new one.

### 1. Implement the alternative

Create `mimosa/components/damages/newdamage.py`:

```python title="mimosa/components/damages/newdamage.py"
from mimosa.common import (
    AbstractModel,
    ModelContext,
    RegionalEquation,
    Var,
)


def get_constraints(m: AbstractModel, context: ModelContext):
    """Example damage specification with no damage costs."""

    m.damage_costs = Var(m.t, m.regions)

    return [
        RegionalEquation(
            m.damage_costs,
            lambda m, t, r: 0.0,
        )
    ]
```

### 2. Register the implementation

Add it to the existing registry in `mimosa/components/damages/__init__.py`:

```python title="mimosa/components/damages/__init__.py" hl_lines="1 6"
from . import coacch, newdamage, nodamage


DAMAGE_MODULES = {
    "COACCH": coacch.get_constraints,
    "nodamage": nodamage.get_constraints,
    "newdamage": newdamage.get_constraints,
}
```

The registry maps the user-facing configuration value to the function that constructs that
implementation. `create_abstract_model` already loads the selected damage implementation from this
registry, so no additional call should be added there.

### 3. Add the configuration choice

Add the same name to the relevant enum in `mimosa/inputdata/config/config_default.yaml`:

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

The registry key and configuration value must match exactly. Users can then select the implementation:

```python
from mimosa import MIMOSA, load_params

params = load_params()
params["model structure"]["damage module"] = "newdamage"
model = MIMOSA(params)
```

The same pattern is used by the emission-trading, financial-transfer, effort-sharing, welfare and
objective registries.

## Reading structural options from `ModelContext`

`ModelContext` provides three methods:

```python
context.module("damage")
context.options("damage")
context.option("damage", "adaptation", default="none")
```

* `module(component)` returns the selected registry entry.
* `options(component)` returns all structural options for that component.
* `option(component, option, default)` returns one option with a fallback value.

Selectable component options are read from `<component> module options`; fixed-component options are
read from `<component> options` under `model structure`. Any supported option must also be defined and
validated in `config_default.yaml`.

Prefer `context.option(...)` to directly indexing `context.components`. This keeps default handling in
one place and makes the component easier to read.

## Testing a component

At minimum, test that:

1. the configuration parser accepts the new module name and any options;
2. `MIMOSA(params, prerun=False)` constructs the model with the new selection;
3. the expected variables and Pyomo constraints exist on `model.concrete_model`;
4. every returned equation can also be evaluated in simulation mode;
5. an existing alternative still constructs correctly, to detect accidental changes to the shared
   module contract.

Equation-heavy components should also test parity between their Pyomo expressions and simulation
equations. Keep tests small: model construction is usually enough for registration tests, while only
behaviour that depends on a solver needs a full optimisation run.
