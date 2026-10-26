# Guided exercise: add a new impact sector

In this exercise, you will add a fictional impact sector: **heat-related damage to
outdoor equipment**. Imagine that hotter conditions increase the cost of repairing
and replacing equipment. We will represent these extra costs with a simple relation
between temperature and economic damages.

The sector and its coefficient are invented for this exercise. The purpose is to
practise adding a model relationship, rather than reproduce an existing impact study.

You will learn how to:

- add a variable and an equation to a prepared component;
- include the new sector in total damages, so it affects GDP;
- make the damage coefficient configurable and compare different assumptions.

## Where to work

Your course branch already contains `mimosa/components/new_component.py`, with the
empty `get_constraints(m, inputs)` function. It is already connected in
`model_builder.py`, so MIMOSA will include your additions automatically.

You will use these files:

```text
mimosa/
├── components/
│   ├── new_component.py        # Add the new sector here
│   └── damages/
│       └── coacch.py           # Include it in total damages
└── inputdata/
    └── config/
        └── config_default.yaml # Define the new parameter here
run_extension.py                # Create this script to run the exercise
```

All paths start from MIMOSA's main directory: the folder containing the `mimosa`
folder and `pyproject.toml`.
This exercise uses the COACCH damage module and assumes your editable copy of MIMOSA
is ready to run.

Inside `get_constraints`, `m` is the model. A **variable** holds a model result, a
**parameter** supplies an assumption, and an **equation** describes how to calculate
one variable from other model quantities.

## Our fictional damage function

We assume that each additional degree of warming causes extra equipment damage
costs equal to **0.2% of gross GDP**:

$$
\text{equipment damage fraction}_{t,r}
= 0.002 \cdot
\left(\href{./#var__temperature}{T_t}
- \href{./#param__temperature.initial}{T_0}\right).
$$

Here $T_t$ is the temperature at timestep $t$, and $T_0$ is the temperature at the
model start. Subtracting $T_0$ makes extra damages zero in the initial year. Under
this simple linear relation, cooling below the initial temperature would give a
benefit, represented by a negative damage value.

We store damages as a **fraction**, so `0.002` means `0.2%`. For example, one degree
of additional warming gives `0.002`, and two degrees give `0.004`, or `0.4%` of GDP.
We use the same damage fraction in every region for this exercise.

## 1. Add a variable

Open `mimosa/components/new_component.py`. The names used below, including `Var`,
`Param` and `RegionalEquation`, are already imported in your starter file.

Inside `get_constraints`, add the following code to define a new variable:

```python hl_lines="3-7"
    # Add your variables and parameters here

    m.equipment_damage_costs = Var(
        m.t,
        m.regions,
        doc="Fictional extra damage costs from heat-sensitive outdoor equipment, as a fraction of gross GDP, relative to the model start.",
    )
```

| Part                       | Meaning                                     |
| -------------------------- | ------------------------------------------- |
| `m.equipment_damage_costs` | The name of the new variable on the model   |
| `Var(m.t, m.regions, ...)` | Store a value for every timestep and region |
| `doc=...`                  | A short description of the variable         |

See [Variables](variables_constraints.md#1-variables) for more ways to define variables.

## 2. Add the damage equation

In the same file, replace the empty `constraints = [...]` block with:

```python
    constraints = [
        RegionalEquation(
            m.equipment_damage_costs,
            lambda m, t, r: 0.002 * (m.temperature[t] - m.T0),
        ),
    ]
```

Keep the existing `return constraints` line below it. This returns your equation to
MIMOSA so it can be used when running the model.

Read `lambda m, t, r: ...` as: **“For this timestep and region, calculate the expression
after the colon.”** MIMOSA applies it to every timestep and region for you.

- `t` identifies a timestep and `r` identifies a region.
- `m.temperature[t]` is the global temperature at that timestep; it has no region index.
- `m.T0` is the initial temperature, which is the same for all timesteps and regions.
- The first argument, `m.equipment_damage_costs`, names the result being calculated
  and is written without `[t, r]`.

See [Equations](variables_constraints.md#2-equations) for more detail on
`RegionalEquation` and the `lambda` notation.

Save `new_component.py` before continuing.

## 3. Run the model and check your calculation

Create `run_extension.py` in MIMOSA's main directory and paste in:

```python title="run_extension.py"
from mimosa import MIMOSA, load_params

params = load_params()

model = MIMOSA(params)
simulation = model.run_simulation()

model.save_simulation(simulation, "guided_exercise")
```

This is a no-policy simulation using all default parameters, regions and timesteps.
Calling `run_simulation()` without control values sets mitigation to zero. This
exercise uses simulation and does not need IPOPT.

Run the script from MIMOSA's main directory:

```bash
python run_extension.py
```

The results are saved to `output/guided_exercise.csv`. You can open this file in
**Excel**, or open the [MIMOSA Dashboard](https://dashboard-mimosa.onrender.com/)
and **drag and drop the CSV file** onto it to explore the results.

In the CSV, the `Variable` and `Region` columns identify each row, and the year
columns contain the results. Your new variable is included automatically. Look for:

| Variable                 | Region   | What to check                                                                                              |
| ------------------------ | -------- | ---------------------------------------------------------------------------------------------------------- |
| `equipment_damage_costs` | `USA`    | Extra damages are zero in 2025 and positive in 2050. Values are fractions of GDP, so `0.002` means `0.2%`. |
| `temperature`            | `Global` | The temperature values in 2025 and 2050 show how much additional warming has occurred.                     |
| `GDP_net`                | `USA`    | Write down the value in the 2050 column to compare after the next step.                                    |

To check your equation using the CSV, subtract the 2025 temperature from the 2050
temperature and multiply by `0.002`. This should match the equipment damage
fraction in the 2050 column, allowing for rounding in the saved values.

At this stage, the new damage variable is calculated and saved. The next step makes
it part of the damages deducted from GDP.

## 4. Include the new sector in total damages

Open `mimosa/components/damages/coacch.py`. Inside `get_constraints`, find the
`RegionalEquation` for `m.damage_costs`. It currently adds `m.non_slr_damage_costs`
and `m.slr_damage_costs`.

Replace **only that equation** with the version below, which adds your new sector.
Keep the other equations and the surrounding list in place:

```python hl_lines="6"
            RegionalEquation(
                m.damage_costs,
                lambda m, t, r: (
                    m.non_slr_damage_costs[t, r]
                    + m.slr_damage_costs[t, r]
                    + m.equipment_damage_costs[t, r]
                ),
            ),
```

The total damage fraction now includes the new equipment damages. The existing
COACCH equations convert total damages to currency units and calculate the global
total. The economic module deducts the total damage costs from GDP, which affects
consumption and welfare as well.

Save `coacch.py` and run `run_extension.py` again. Reopen the CSV in Excel or load
the new file into the dashboard. Check the equipment damage value and compare
`GDP_net` for the USA in 2050 with the value you wrote down. It should be lower
when the extra damages are included. Each run replaces the previous
`output/guided_exercise.csv` file.

For this exercise, we treat the fictional equipment sector as an additional impact
that is not already included in the COACCH damage functions.

## 5. Make the damage coefficient configurable

The value `0.002` is currently written directly in the equation. We will turn it
into a parameter so you can choose a different value from your run script.

Open `mimosa/inputdata/config/config_default.yaml`. Find `economics:`, then the
existing `damages:` section beneath it. Add `equipment_damage_coefficient` at the
same indentation level as `scale factor`:

```yaml
economics:
  damages:
    equipment_damage_coefficient:
      descr: Fictional equipment damage fraction per degree of additional warming
      type: float
      min: 0
      default: 0.002
```

Keep the existing `economics:` and `damages:` headings and all their other entries.
Only add the new parameter entry.

`type: float` means the value is a decimal number, and `min: 0` prevents a negative
coefficient. We interpret the number as the damage fraction per additional degree
of warming. The default remains `0.002`.

See [Adding parameters from configuration](parameters.md#config-params) for more
detail on defining a new configuration entry.

In `new_component.py`, add this declaration **above `constraints = [...]`**, alongside
your variable declaration:

```python
    m.equipment_damage_coefficient = Param(
        initialize=inputs.config("economics.damages.equipment_damage_coefficient"),
        doc="Fictional equipment damage fraction per degree of warming above the model's initial temperature.",
    )
```

`inputs.config(...)` reads the value from the configuration. Its name on the model
is `m.equipment_damage_coefficient`, and it has the same value for every timestep
and region.

Finally, replace the `constraints = [...]` block in `new_component.py` with:

```python
    constraints = [
        RegionalEquation(
            m.equipment_damage_costs,
            lambda m, t, r: m.equipment_damage_coefficient * (m.temperature[t] - m.T0),
        ),
    ]
```

Save both files and run the script again. The results should match your previous
run when you open the new CSV in Excel or the dashboard: you have changed where
the coefficient comes from, while keeping its value at `0.002` per degree.

## 6. Try a stronger damage assumption

Replace the contents of `run_extension.py` with the complete script below. The
highlighted lines change the coefficient and save this run with a different filename:

```python title="run_extension.py" hl_lines="4 9"
from mimosa import MIMOSA, load_params

params = load_params()
params["economics"]["damages"]["equipment_damage_coefficient"] = 0.004

model = MIMOSA(params)
simulation = model.run_simulation()

model.save_simulation(simulation, "guided_exercise_stronger_damages")
```

This doubles the damage fraction assigned to a given amount of additional warming:
from `0.2%` to `0.4%` of GDP per degree. Save and rerun the script. The new results
are saved to `output/guided_exercise_stronger_damages.csv`, keeping the original
`output/guided_exercise.csv` available for comparison.

Open both files in Excel, or drag and drop both into the
[MIMOSA Dashboard](https://dashboard-mimosa.onrender.com/). Compare
`equipment_damage_costs` and `GDP_net` for the same region and year. You can now
change this assumption without editing the component or its configuration defaults.

As a second check, set the coefficient to `0` in the parameter line and rerun. In
the new CSV, `equipment_damage_costs` should be zero in every year.

For more ways to supply parameter values, including regional data, see
[Adding parameters and data](parameters.md).

??? info "Check your completed component"

    Your completed `mimosa/components/new_component.py` should look like this:

    ```python
    from mimosa.common import (
        ConcreteModel,
        RegionalEquation,
        GlobalEquation,
        Var,
        Param,
    )

    from mimosa.core.model_inputs import ModelInputs


    def get_constraints(m: ConcreteModel, inputs: ModelInputs):
        """Fictional heat-related equipment damages for the guided exercise."""

        m.equipment_damage_costs = Var(
            m.t,
            m.regions,
            doc="Fictional extra damage costs from heat-sensitive outdoor equipment, as a fraction of gross GDP, relative to the model start.",
        )
        m.equipment_damage_coefficient = Param(
            initialize=inputs.config("economics.damages.equipment_damage_coefficient"),
            doc="Fictional equipment damage fraction per degree of warming above the model's initial temperature.",
        )

        constraints = [
            RegionalEquation(
                m.equipment_damage_costs,
                lambda m, t, r: m.equipment_damage_coefficient * (m.temperature[t] - m.T0),
            ),
        ]

        return constraints
    ```
