# Extending MIMOSA

## General form of the model

MIMOSA is built with [Pyomo](https://www.pyomo.org/), an open-source optimisation modelling
package. The model combines variables and parameters with equations that calculate model outcomes
and constraints that restrict the feasible solution. The selected [objective
module](../components/welfare.md#optimisation-goal-and-discounting) either maximises discounted
welfare or minimises discounted global costs.

The following pages explain how to add variables, equations, constraints, parameters and complete
model components. They focus on the conventions used in MIMOSA rather than providing a general
introduction to Pyomo.

MIMOSA's shared Pyomo `ConcreteModel`, time and region sets, and baseline inputs are created in
`mimosa/base_model.py`. The components listed in `mimosa/model_builder.py` then add their variables,
parameters, equations and constraints to this shared object, which is always called `m`:

```python
m = create_base_model(inputs)
```

The preprocessor prepares configuration and data lookup before construction. Base sets and
parameters are immediately available; components add initialized parameters and variables in
catalogue order. Collected constraints and the objective are attached after all declarations.
There is no separate abstract-model instantiation or parameter loading from `doc`.

!!! info "A note about file structure"

    After forking and cloning MIMOSA to your computer, you will find a file structure that looks like this:

    ```python title="MIMOSA file structure"
    mimosa/
    ├── model_builder.py # (1)!
    ├── base_model.py # (2)!
    ├── mimosa.py
    ├── components/ # (3)!
    │   ├── emissions.py
    │   ├── mitigation.py
    │   └── ...
    └── inputdata/
        ├── config/
        │   └── config_default.yaml # (4)!
        ├── regionalparams/
        └── data/

    run.py # (5)!

    ```

    1.  The model components are listed and combined in this file.
    2.  Shared time, region and baseline input parameters are defined in this file.
    3.  The components discussed in the [Model documentation](../components/index.md) are defined in this folder.
    4.  Configuration parameter types and default values are defined in this file.
    5.  Example of a basic model run. Place your run files here, such that the mimosa package from this folder is used,
        and not a version previously installed through `pip install mimosa`.

For most extensions, use the following steps:

1. [Create a new component](components.md) (`optional`, only necessary if the extension is a new module)
2. [Add new variables and constraints to the model](variables_constraints.md)
3. [Add new parameters and data to the model](parameters.md)

For more advanced extensions, see [Selectable modules](selectable_modules.md) and
[Model options](model_options.md).
