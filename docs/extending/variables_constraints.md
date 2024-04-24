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

The relationships between variables are defined through constraints. Constraints are Python functions (often lambda functions)
that represent the underlying equations of the model. In our example, a constraint would relate the carbon intensity to the
emissions and the GDP:

```python
RegionalConstraint(
    lambda m, t, r: m.carbon_intensity[t, r] == m.regional_emissions[t, r] / m.GDP_net[t, r],
    name="carbon_intensity"
)
```

The constraint consists of two parts: the lambda function with the equation, and the name of the constraint. Note that the lambda
function always has the model `m` as the first argument, followed by the indices of the variables that the constraint relates.

There are four types of constraints, depending on whether they depend on regions, time, or both:

- Region and time dependent:

    `RegionalConstraint(lambda m, t, r: ..., name="...")`

- Only region dependent:

    `RegionalInitConstraint(lambda m, r: ..., name="...")`

- Only time dependent, not on region:
    
    `GlobalConstraint(lambda m, t: ..., name="...")`

- Not dependent on time nor on region:

    `GlobalInitConstraint(lambda m: ..., name="...")`

Next, MIMOSA needs to know where the constraints are created. Every component therefore consists of a function called `get_constraints()` (see [Components](components.md)). This function returns a list of constraints. Add the new constraint to the list:

```python hl_lines="5 6 7 8 9 10 11"
def get_constraints(m):
    constraints = []
    # ... existing code ...
    
    constraints.extend([
        RegionalConstraint(
            lambda m, t, r: m.carbon_intensity[t, r] == m.regional_emissions[t, r] / m.GDP_net[t, r],
            name="carbon_intensity"
        ),
        ...
    ])

    return constraints
```

**Note:** as shown in this example, constraints do not need to be equality constraints. They can also be inequality constraints. Also, 
constraints do need to be in the form of `m.variable == expression`: the left-hand-side and the right-hand-side can be non-linear combinations of variables and parameters.

#### Conditionally skip constraints

If a constraint should only be enforced under certain conditions, you can use an the `Constraint.Skip` statement. This can be for certain time periods, regions, or any condition based on parameters. It is not possible to skip constraints based on variable values.

```python hl_lines="4 5"
GlobalConstraint(
    lambda m, t: (
        m.global_emissions[t] <= 0
        if m.year(t) > 2100
        else Constraint.Skip
    ),
    name="net_zero_after_2100",
)
```

**Note:** the variable `t` is a time index (starting at `t=0`), and `m.year(t)` returns the year of the time index `t`.


## Advanced: soft-equality constraints

## Advanced: numerical stability

* Avoid division by zero: add a small number to the denominator
* Avoid large numbers: scale the variables by choosing appropriate units
* Avoid negative numbers in exponents and square roots by using the `soft_min` and `soft_max` functions