# Creating model components

Create a new component when an extension adds a coherent part of the model with its own variables,
parameters and equations. If the change only adds one or two equations to an existing subject area,
it is usually clearer to add them to the existing component instead.

This page describes the most common case: adding a component that is always part of MIMOSA. This does
not require changes to the configuration of the model or the use of `ModelContext` options.

## Basic structure of a component

A component is a Python file with a function called `get_constraints`:

```python title="mimosa/components/new_component.py"
from mimosa.common import (
    AbstractModel,
    GlobalEquation,
    Var,
)


def get_constraints(m: AbstractModel, context):
    """Calculate the square of global temperature for every time step."""

    m.temperature_squared = Var(m.t)

    return [
        GlobalEquation(
            m.temperature_squared,
            lambda m, t: m.temperature[t] ** 2,
        )
    ]
```

The function does three things:

1. It adds the component's Pyomo `Param`, `Var` and related objects to the shared model `m`.
2. It describes the equations and constraints that define those variables.
3. It returns those equations and constraints, so MIMOSA can add them to the Pyomo model and use the
   equations in simulation mode.

Every component function receives both `m` and `context`. A basic component does not need to use
`context`; it only needs to include it in the function definition because MIMOSA supplies it when the
component is added. More advanced uses are described under [Selectable modules](selectable_modules.md)
and [Model options](model_options.md).

`GlobalEquation` and `RegionalEquation` are used in both the Pyomo model and simulation mode. Other
constraints only affect the Pyomo model. See [Variables, equations and constraints](variables_constraints.md)
for the available forms, an explanation of the `lambda` syntax, and complete examples of global and
regional variables.

## 1. Create the component file

Add a Python file to `mimosa/components`:

```text hl_lines="7"
mimosa/
├── abstract_model.py
├── base_model.py
└── components/
    ├── emissions.py
    ├── mitigation.py
    ├── new_component.py
    └── ...
```

Define the component's variables, parameters, equations and constraints inside `get_constraints`.
Variables and constraint names must be unique within MIMOSA's shared model.

When the component needs a new parameter, follow [Adding parameters and data](parameters.md) to connect
the Pyomo `Param` to a configuration value or input file.

## 2. Add the component to MIMOSA

Import and register the component in the component catalogue in `mimosa/abstract_model.py`:

```python title="mimosa/abstract_model.py" hl_lines="3 10"
from mimosa.components import (
    emissions,
    new_component,
    # ...
)


MODEL_COMPONENTS = (
    fixed_component("emissions", emissions.get_constraints),
    fixed_component("new_component", new_component.get_constraints),
    # ... remaining components ...
)
```

Place the entry near related model components so the construction sequence remains easy to understand.
References inside equation functions are evaluated after the model components have been added, so their
dependencies do not normally determine the order of these entries.

That is all that is required for a component that should always be included. There is no need to add
the component anywhere else. There is also no need to change `config_default.yaml` unless users need
to choose between different versions or the component needs options while the model is being put
together.

## 3. Document the component

Write the explanation of the component in the docstring of `get_constraints`. MkDocs can include this
docstring directly in the model documentation:

```markdown
:::mimosa.components.new_component.get_constraints
```

For model components, the docstring should preferably explain:

- what the component represents;
- the main equations and the meaning of their variables;
- which parameters a modeller can change;
- any numerical approximations or limitations;
- a short usage example when the component needs special settings.

Keeping this explanation next to the equations makes it less likely that the scientific documentation
and implementation drift apart.

## 4. Test the component

At minimum, test that:

1. `MIMOSA(params, prerun=False)` can construct a model containing the new component;
2. the expected variables and Pyomo constraints exist on `model.concrete_model`;
3. returned equations can be evaluated in simulation mode.

Equation-heavy components should also compare the values of their Pyomo expressions with the values
calculated in simulation mode. Keep construction tests small; only behaviour that depends on a solver
needs a full optimisation run.

## More advanced components

Continue with:

- [Selectable modules](selectable_modules.md) when users should be able to choose between alternative
  versions of a component, or when adding a new submodule to an existing group such as damages,
  welfare or effort sharing;
- [Model options](model_options.md) when a setting changes which variables or equations a component
  creates.
