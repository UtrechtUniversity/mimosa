## Forking MIMOSA from GitHub

## General form of the model

MIMOSA is built as a [Pyomo](https://www.pyomo.org/) model: an open-source Python package optimisation modelling language. 
Pyomo models consist of a combination of variables, constraints and parameters. The constraints link together the variables
in the form of (optionally) non-linear equations. One variable is defined as the optimisation objective: in MIMOSA's case, 
the net present value of the global welfare. Pyomo translates the combination of variables, constraints and parameters to
a form suitable for an external solver. The solver maximises the objective variable, while trying to fulfill all the 
constraints.

On this page, we give examples of how to extend MIMOSA by adding new variables and constraints, by adding new parameters,
and by creating completely new model components (modules). The basis of MIMOSA is a Pyomo `AbstractModel`: a model object
where all variables and other components will be added to and which will be sent to the solver. In `mimosa/abstract_model.py`,
this object is created:

```python
m = AbstractModel()
```

This model will always be referred to as `m`.

???+ info "A note about file structure"

    After forking and cloning MIMOSA to your computer, you will find a file structure that looks like this:

    ```python title="MIMOSA file structure"
    mimosa
    │   abstract_model.py # (1)!
    │   mimosa.py
    │
    └─── components # (2)!
        │   emissions.py
        │   mitigation.py
        │   ...
    │
    └─── inputdata
        │
        └─── config / config_default.yaml # (3)!
        │
        └─── regionalparams / ...
        │
        └─── data / ...

    run.py # (4)!
    
    ```
    
    1.  All the model components are tied together in this file
    2.  The different components discussed in the [Model documentation](../components/general.md) pages are defined in the
        Python files in this folder
    3.  All parameters types and default values are defined in this file
    4.  Example of a basic model run. Place your run files here, such that the mimosa package from this folder is used,
        and not a version previously installed through `pip install mimosa`.

    The files you are most likely to edit are highlighted. The different components discussed in the
    [Model documentation](../components/general.md) pages are defined in the Python files in the folder
    [`mimosa/components`]({{config.repo_url}}/tree/master/mimosa/components). All these modules are tied
    together in the file [`mimosa/abstract_model.py`]({{config.repo_url}}/blob/master/mimosa/abstract_model.py).