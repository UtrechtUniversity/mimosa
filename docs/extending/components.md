When the extension to MIMOSA is significant, it is recommended to create a new component. This
component will contain all the new variables, constraints, and parameters that are part of the
module.

### Create the new component

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

A component always consists of a function `get_constraints(m)`, in which all the new variables, parameters, and constraints are defined. The function needs to return a list of all the newly created constraints:

```python title="mimosa/components/new_component.py"
from mimosa.common import (
    AbstractModel, Param, Var,
    GlobalConstraint, GlobalInitConstraint,
    RegionalConstraint, RegionalInitConstraint,
    quant
)

def get_constraints(m: AbstractModel):
    """
    Documentation of what the new component does
    """

    # New variables
    m.new_var = Var()
    
    # New parameters
    m.new_param = Param()
    
    # Create a list of all the new constraints
    constraints = [
        GlobalConstraint(...),
        ...
    ]
    
    # Return the list of constraints
    return constraints
```

### Link the new component to the model

To link the new component to the model, import the new component in `mimosa/abstract_model.py`:
    
```python title="mimosa/abstract_model.py" hl_lines="1 13"
from mimosa.components import new_component

def create_model():
    m = AbstractModel()
    
    # ... existing code ...

    ######################
    # Components
    ######################
    
    # Add the new component
    constraints.extend(new_component.get_constraints(m))
    
    # ... existing code ...
    
    return m
```

