When the extension to MIMOSA is significant, it is recommended to create a new component. This
component will contain all the new variables, constraints, and parameters that are part of the
module.

As an example, we will create a new component called "New component". To do this, create a new file
in the `mimosa/components` folder called `new_component.py`:

```python title="MIMOSA file structure: create a new file" hl_lines="8"
mimosa
│   abstract_model.py
│   mimosa.py
│
└─── components
    │   emissions.py
    │   mitigation.py
    │   new_component.py
    │   ...
│
└─── inputdata
    │   ...

```