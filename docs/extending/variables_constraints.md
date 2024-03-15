## Variables

Let's create a new variable that calculates the regional carbon intensity (emissions divided by GDP).
You can add this variable to any of the components in the folder `mimosa/components`, but the most logical place is probably
the file [`mimosa/components/cobbdouglas.py`]({{config.repo_url}}/blob/master/mimosa/components/cobbdouglas.py), which contains
all GDP-related variables and constraints. Each component has a function `get_constraints(...)`, which is called from the main
`abstract_model.py` file.

Inside the function `get_constraints()`, create the new variable `m.carbon_intensity`:

```python title="mimosa/components/cobbdouglas.py" hl_lines="5"
def get_constraints(m):
    # ... existing code ...
    
    # New variable
    m.carbon_intensity = Var(m.t, m.regions)
    
    # ... existing code ...
```

If the variable is not dependent on either time or region, remove the `m.t` or `m.regions` from the variable definition.


## Constraints
