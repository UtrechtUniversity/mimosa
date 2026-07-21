The MIMOSA model, like any model, consists of variables that are linked together by equations.
More advanced relationships that cannot be written as MIMOSA equations are introduced later on this
page.

## 1. Variables

Let's create a new variable that calculates the regional carbon intensity (emissions divided by GDP).
You can add this variable to any of the components in the folder `mimosa/components`, but the most logical place is probably
the file [`mimosa/components/cobbdouglas.py`]({{config.repo_url}}/blob/master/mimosa/components/cobbdouglas.py), which contains
all GDP-related variables and equations. Each component has a function `get_constraints(...)`, which is called from the main
`abstract_model.py` file.

Inside the function `get_constraints()`, create the new variable `m.carbon_intensity`:

```python title="mimosa/components/cobbdouglas.py" hl_lines="5"
def get_constraints(m, context):
    # ... existing code ...

    # New variable
    m.carbon_intensity = Var(m.t, m.regions)

    # ... existing code ...
```

`m.t` and `m.regions` are the two shared index sets used most often in MIMOSA. `m.t`
contains the model's time steps and `m.regions` contains its region names. Pass the sets on
which a variable depends to `Var`:

```python
m.global_constant = Var()                    # One value
m.global_by_time = Var(m.t)                  # One value per time step
m.regional_constant = Var(m.regions)         # One value per region
m.regional_by_time = Var(m.t, m.regions)     # One value per time step and region
```

The order of the sets determines the order used when accessing a value. For example,
`m.regional_by_time[t, r]` matches `Var(m.t, m.regions)`.

!!! warning "Use `m.regions`, not `m.r`, in a variable definition"

    There is no standard model set called `m.r`. In later equation functions, `r` is only the
    local name for the current member of `m.regions`, just as `t` is the current member of `m.t`.

    ```python
    m.carbon_intensity = Var(m.t, m.regions)  # Correct: declare using model sets

    lambda m, t, r: m.carbon_intensity[t, r]  # Here r is one current region
    ```

    A helpful way to read the second line is: “for this model, time step and region, return this
    expression.” The local index could technically have another name, but MIMOSA consistently uses
    `t` and `r` for readability.

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

**Important note:** the left-hand side should be specified _without_ the indices (`t`, `r`): it should be just the variable (e.g. `m.carbon_intensity`, not <span style="text-decoration: line-through; text-decoration-color: rgba(0,0,0,.25);" markdown>`m.carbon_intensity[t, r]`</span>)

### What the `lambda` function does

`lambda` is Python syntax for a short, unnamed function. MIMOSA stores this function and calls it
once for every relevant index when it builds an optimisation model or runs a simulation. It is not a
MIMOSA parameter and it is not evaluated when the `RegionalEquation` is first written.

For example, these two definitions mean the same thing:

=== "Short `lambda` form"

    ```python
    RegionalEquation(
        m.carbon_intensity,
        lambda m, t, r: m.regional_emissions[t, r] / m.GDP_net[t, r],
    )
    ```

=== "Equivalent named function"

    ```python
    def calculate_carbon_intensity(m, t, r):
        return m.regional_emissions[t, r] / m.GDP_net[t, r]


    RegionalEquation(m.carbon_intensity, calculate_carbon_intensity)
    ```

The arguments must match the equation type:

| Equation type      | Function arguments | Called for                 |
| ------------------ | ------------------ | -------------------------- |
| `RegionalEquation` | `m, t, r`          | every time step and region |
| `GlobalEquation`   | `m, t`             | every time step            |

Here `m` is the shared MIMOSA model, while `t` and `r` are the current values drawn from `m.t` and
`m.regions`. Use a named function instead of `lambda` when the calculation needs several statements,
is reused, or deserves its own explanation or test.

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

Next, MIMOSA needs to receive the equation from the component. Every component uses a function named
`get_constraints()` (see [Components](components.md)); despite its general name, this function also
returns MIMOSA equations. Add the new equation to the returned list:

```python hl_lines="5 6 7 8 9 10 11"
def get_constraints(m, context):
    equations = []
    # ... existing code ...

    equations.extend([
        RegionalEquation(
            m.carbon_intensity,  # Name of the left-hand-side variable
            lambda m, t, r: m.regional_emissions[t, r] / m.GDP_net[t, r]  # Right-hand-side expression
        ),
        ...
    ])

    return equations
```

## 3. Advanced: general constraints

There are situations where the relationship between variables cannot be expressed as an equation:

- The relationship is not a simple equality, but an inequality (e.g. `x >= y`).
- The left-hand-side and right-hand-side contain the same variable, but not in a way that can be expressed as an equation.
- The left-hand-side contains more than one variable (e.g. `sqrt(x + y) = sin(z)`).

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

As with equations, the arguments of each `lambda` identify the model and the indices for which
MIMOSA calls it: `m` is the shared model, `t` is a member of `m.t`, and `r` is a member of
`m.regions`.

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
effort-sharing regime requires attributed mitigation costs as a share of GDP to remain close to a
common global level:

```python
RegionalSoftEqualityConstraint(
    lambda m, t, r: m.mitigation_costs[t, r],
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

## 5. Advanced: smooth helper functions and numerical stability

### `soft_switch` (softswitch), `soft_min` and `soft_max`

Optimisation variables are symbolic while the model is constructed. Therefore, Python branching
such as `if x > 0`, and Python's `min()` and `max()`, cannot be used when `x` is a Pyomo variable.
Sharp piecewise functions can also make a non-linear optimisation problem harder to solve. MIMOSA
exports three smooth approximations from `mimosa.common`. The function sometimes informally called
“softswitch” is named `soft_switch` in Python:

| Helper                       | Smooth approximation       | Typical use                                  |
| ---------------------------- | -------------------------- | -------------------------------------------- |
| `soft_switch(x, scale)`      | 0 when $x<0$, 1 when $x>0$ | Smoothly turn a term on around $x=0$         |
| `soft_min(x, scale)`         | $\max(0,x)$                | Keep a quantity approximately non-negative   |
| `soft_max(x, maxval, scale)` | $\min(x,\text{maxval})$    | Cap a quantity at an approximate upper limit |

The names `soft_min` and `soft_max` describe the bound being applied: `soft_min` applies a lower
bound of zero, while `soft_max` applies the supplied upper bound. They are approximations, so their
results differ slightly from the exact piecewise functions, especially close to the transition.

```python
from mimosa.common import soft_max, soft_min, soft_switch

# Approximately include extra_cost only when net_emissions is positive.
active_cost = soft_switch(net_emissions, scale=10) * extra_cost

# Approximately max(0, net_emissions).
positive_emissions = soft_min(net_emissions, scale=10)

# Approximately min(exponent, 10), to avoid overflow in exp(exponent).
safe_exponent = soft_max(exponent, maxval=10, scale=0.1)
```

`scale` should be the approximate magnitude of `x` near which the transition may occur, expressed in
the same units as `x`. A smaller scale makes the transition around zero sharper; a larger scale makes
it more gradual. For example, use `scale=10` if meaningful changes in `x` near zero are normally of
order 10, and `scale=0.01` if they are normally of order 0.01. Check the approximation over the
expected range rather than accepting the default `scale=1.0` automatically.

Use these helpers only when a smooth approximation is scientifically acceptable and a small value
beyond the intended boundary will not invalidate the model. Prefer:

- a variable bound, such as `Var(bounds=(0, None))`, when the quantity must never be negative;
- an exact inequality constraint when a limit must be enforced rather than approximated;
- an ordinary Python `if`, `min` or `max` when the input is a known Python/configuration value rather
  than a Pyomo variable.

Document the reason, chosen scale and acceptable approximation error beside each use. `soft_switch`
is not a binary decision and should not be used when the model requires an exact on/off state.

### General numerical guidance

Non-linear optimisation is sensitive to scale and to functions that are undefined or non-smooth in
part of their domain. When adding equations and constraints:

- Choose [units](units.md) that keep typical variable and constraint values at manageable scales.
- Give variables meaningful bounds when their valid range is known.
- Avoid division by values that can reach zero and powers, logarithms or square roots outside their
  valid domain.
- Use the smooth helper functions described above only where a documented approximation is
  scientifically acceptable.
- Provide sensible initial values for variables in difficult non-linear equations.
- Do not add an arbitrary small number to a denominator without checking how it changes the equation
  and its units.

Numerical workarounds are part of the model formulation. Explain them beside the equation and test
their behaviour over the expected input range.
