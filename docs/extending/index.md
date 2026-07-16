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

MIMOSA starts with a Pyomo `AbstractModel` in `mimosa/abstract_model.py`. Variables, parameters,
equations and constraints from all model components are added to this shared object, which is always
called `m`:

```python
m = AbstractModel()
```

!!! info "A note about file structure"

    After forking and cloning MIMOSA to your computer, you will find a file structure that looks like this:

    ```python title="MIMOSA file structure"
    mimosa/
    ├── abstract_model.py # (1)!
    ├── mimosa.py
    ├── components/ # (2)!
    │   ├── emissions.py
    │   ├── mitigation.py
    │   └── ...
    └── inputdata/
        ├── config/
        │   └── config_default.yaml # (3)!
        ├── regionalparams/
        └── data/

    run.py # (4)!

    ```

    1.  The model components are combined in this file.
    2.  The components discussed in the [Model documentation](../components/index.md) are defined in this folder.
    3.  Configuration parameter types and default values are defined in this file.
    4.  Example of a basic model run. Place your run files here, such that the mimosa package from this folder is used,
        and not a version previously installed through `pip install mimosa`.

For most extensions, use the following steps:

1. [Create a new component](components.md) (`optional`, only necessary if the extension is a new module)
2. [Add new variables and constraints to the model](variables_constraints.md)
3. [Add new parameters and data to the model](parameters.md)

For more advanced extensions, see [Selectable modules](selectable_modules.md) and
[Model options](model_options.md).
