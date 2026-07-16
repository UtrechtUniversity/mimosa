The MIMOSA model, like any model, consists of variables that are linked together by equations and constraints. 

## 1. Variables

Let's create a new variable that calculates the regional carbon intensity (emissions divided by GDP).
You can add this variable to any of the components in the folder `mimosa/components`, but the most logical place is probably
the file [`mimosa/components/cobbdouglas.py`]({{config.repo_url}}/blob/master/mimosa/components/cobbdouglas.py), which contains
all GDP-related variables and constraints. Each component has a function `get_constraints(...)`, which is called from the main
`abstract_model.py` file.

Inside the function `get_constraints()`, create the new variable `m.carbon_intensity`:

```python title="mimosa/components/cobbdouglas.py" hl_lines="5"
def get_constraints(m, context):
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
def get_constraints(m, context):
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

In these cases, you can use a general constraint. It does not define one variable as the
left-hand side of an equation. Instead, its function returns a symbolic Pyomo equality or
inequality expression. The optimiser searches for variable values for which that relation is
satisfied.

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



As shown in this example, constraints can be equalities or inequalities. They do **not** need to
have the form `m.variable == expression`: both sides can contain combinations of variables and
parameters.

Unlike `GlobalEquation` and `RegionalEquation`, general constraints are only passed to the Pyomo
optimisation model. They are not executed in [simulation mode](../run/simulation.md).

<br>

##### Conditionally skip constraints

If a constraint should only be enforced under certain conditions, use `Constraint.Skip`. This can
depend on the timestep, region or parameter values. It cannot depend on the value of an optimisation
variable, because that value is not known while the constraint is being constructed.

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


## 4. Advanced: soft-equality constraints {id="soft-equality-constraints"}

Some modelling conditions should be almost equal but should not be added as another set of exact
equalities. MIMOSA provides `GlobalSoftEqualityConstraint` and
`RegionalSoftEqualityConstraint` for this purpose. A relative soft equality

$$
\text{LHS} \approx \text{RHS}
$$

is converted into two inequalities:

$$
(1-\epsilon)\,\text{RHS}
\leq \text{LHS}
\leq (1+\epsilon)\,\text{RHS}.
$$

The default tolerance is $\epsilon=0.005$, or 0.5%. For example, the equal-mitigation-costs
effort-sharing regime requires regional mitigation costs as a share of GDP to remain close to a
common global level:

```python
RegionalSoftEqualityConstraint(
    lambda m, t, r: m.rel_mitigation_costs[t, r],
    lambda m, t, r: m.effort_sharing_common_level[t],
    name="effort_sharing_regime_mitigation_costs",
    epsilon=0.005,
)
```

A relative tolerance assumes that the right-hand side is non-negative. If the target can be zero or
negative, use an absolute tolerance instead.

Effort-sharing conditions are applied for every region, while regional allowances, costs and trading
balances are already linked by the main model equations and global accounting constraints. Adding
every effort-sharing condition as an exact equality can therefore create too many or redundant
equalities relative to the available variables. IPOPT requires sufficient degrees of freedom and a
well-behaved equality-constraint Jacobian; an overdetermined or linearly dependent equality system
can stop before the optimisation starts.

The soft formulation expresses the intended allocation as a narrow feasible interval instead. Its
bounds are inequalities rather than exact equalities, and the small interval also avoids requiring
numerically exact agreement between regions.

Use `absolute_epsilon` instead when a fixed tolerance in the unit of the quantity is clearer:

```python
RegionalSoftEqualityConstraint(
    lambda m, t, r: calculated_allowances(m, t, r),
    lambda m, t, r: m.regional_emission_allowances[t, r],
    name="regional_allowances",
    absolute_epsilon=0.001,
)
```

This enforces $\text{RHS}-0.001 \leq \text{LHS} \leq \text{RHS}+0.001$. Choose and
document a tolerance that is small for the model quantity but not smaller than the numerical
precision the optimisation can reliably achieve.

## 5. Advanced: numerical stability

Non-linear optimisation is sensitive to scale and to functions that are undefined or non-smooth in
part of their domain. When adding equations and constraints:

- Choose [units](units.md) that keep typical variable and constraint values at manageable scales.
- Give variables meaningful bounds when their valid range is known.
- Avoid division by values that can reach zero and powers, logarithms or square roots outside their
  valid domain.
- Use MIMOSA's smooth `soft_min` and `soft_max` approximations where a documented approximation is
  scientifically acceptable. Do not use Python's `min`, `max` or a conditional based on a Pyomo
  variable.
- Provide sensible initial values for variables in difficult non-linear equations.
- Do not add an arbitrary small number to a denominator without checking how it changes the equation
  and its units.

Numerical workarounds are part of the model formulation. Explain them beside the equation and test
their behaviour over the expected input range.
