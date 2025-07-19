The MIMOSA model, like any model, consists of variables that are linked together by equations and constraints. 

## 1. Variables

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

If the variable is not dependent on either time or region, remove the `m.t` or `m.regions` from the variable definition:

```python
m.variable_name1 = Var()        # No time or region dependency
m.variable_name2 = Var(m.t)     # Time dependent, not region dependent
```


## 2. Equations

Most of the relationships between variables are in the form of `variable(t, r) = fct(other_var1, other_var2, ...)`.
These equations are implemented in MIMOSA as Equations: either `GlobalEquation` (for time-dependent equations) or
`RegionalEquation` (for time- and region-dependent equations). In our example, the carbon intensity equation

$$
\text{carbon intensity}_{t,r} = \frac{\text{regional emissions}_{t,r}}{\text{GDP}_{t,r}}
$$

would be implemented as a `RegionalEquation`:

```python hl_lines="2 3"
RegionalEquation(
    m.carbon_intensity,  # Name of the left-hand-side variable
    lambda m, t, r: m.regional_emissions[t, r] / m.GDP_net[t, r]  # Right-hand-side expression
)
```

**Important note:** the left-hand side should be specified *without* the indices (`t`, `r`): it should be just the variable (e.g. `m.carbon_intensity`, not <span style="text-decoration: line-through; text-decoration-color: rgba(0,0,0,.25);" markdown>`m.carbon_intensity[t, r]`</span>)

Similarly, a global equation (not dependent on region) would be defined as:

```python hl_lines="2 3"
GlobalEquation(
    m.temperature,  # Name of the left-hand-side variable
    lambda m, t: m.T0 + m.TCRE * m.global_emissions[t]  # Right-hand-side expression
)
```

<br>

##### Circular dependencies

Since these equations will also be used in simulation mode, it is important that the right-hand-side expression doesn't contain
the variable from the left-hand-side, to avoid circular dependencies. It is, however, allowed to refer to a previous time step
of the variable:

```python title="✅ Valid equation (reference to previous time step)" hl_lines="4"
GlobalEquation(
    m.cumulative_emissions,
    lambda m, t: (
        m.cumulative_emissions[t - 1] + m.dt * m.global_emissions[t]
        if t > 0 else m.global_emissions[t]
    )
)
```

```python title="❌ Invalid equation (reference to the variable itself)" hl_lines="4"
GlobalEquation(
    m.cumulative_emissions,
    lambda m, t: (
        m.cumulative_emissions[t] ** 2 + m.global_emissions[t]
    )
)
```

<br>

##### Where to place the equations

Next, MIMOSA needs to know where the constraints are created. Every component therefore consists of a function called `get_constraints()` (see [Components](components.md)). This function returns a list of equations/constraints. Add the new constraint to the list:

```python hl_lines="5 6 7 8 9 10 11"
def get_constraints(m):
    constraints = []
    # ... existing code ...
    
    constraints.extend([
        RegionalEquation(
            m.carbon_intensity,  # Name of the left-hand-side variable
            lambda m, t, r: m.regional_emissions[t, r] / m.GDP_net[t, r]  # Right-hand-side expression
        ),
        ...
    ])

    return constraints
```

## 3. Advanced: general constraints

There are situations where the relationship between variables cannot be expressed as an equation:

* The relationship is not a simple equality, but an inequality (e.g. `x >= y`).
* The left-hand-side and right-hand-side contain the same variable, but not in a way that can be expressed as an equation.
* The left-hand-side contains more than one variable (e.g. `sqrt(x + y) = sin(z)`).

In these cases, you can use a general constraint. They do not have a left-hand-side and right-hand-sie explicitly, but
are defined as a lambda function that returns a boolean value. The general constraint is then satisfied if the
lambda function returns `True`. If it returns `False`, the constraint is violated.

For example, to create a constraint to enforce a maximum carbon budget, you can use the following code:

```python
GlobalConstraint(
    lambda m, t: m.cumulative_emissions[t] <= m.carbon_budget,
    name="carbon_budget"
)
```

There are four types of constraints, depending on whether they depend on regions, time, or both:

- Region and time dependent:

    `RegionalConstraint(lambda m, t, r: ..., name="...")`

- Only region dependent:

    `RegionalInitConstraint(lambda m, r: ..., name="...")`

- Only time dependent, not on region:
    
    `GlobalConstraint(lambda m, t: ..., name="...")`

- Not dependent on time nor on region:

    `GlobalInitConstraint(lambda m: ..., name="...")`



**Note:** as shown in this example, constraints do not need to be equality constraints. They can also be inequality constraints. Also, 
constraints do need to be in the form of `m.variable == expression`: the left-hand-side and the right-hand-side can be non-linear combinations of variables and parameters.

<br>

##### Conditionally skip constraints

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


## 4. Advanced: soft-equality constraints

## 5. Advanced: numerical stability

* Avoid division by zero: add a small number to the denominator
* Avoid large numbers: scale the variables by choosing appropriate units
* Avoid negative numbers in exponents and square roots by using the `soft_min` and `soft_max` functions