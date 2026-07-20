---
title: "Running MIMOSA for Assignment 4"
audience: "Students"
status: "Course guide draft"
model_version: "feat_accreu_adaptation_sectoral_damages"
---

# Running MIMOSA for Assignment 4

## A student guide to simulations, optimizations, scenarios, and reproducible analysis

> **Course version**
>
> This guide targets the course distribution based on the `feat_accreu_adaptation_sectoral_damages` version of MIMOSA. Use the provided course environment and notebook. Parameter names and available outputs may differ in other MIMOSA versions.

## 1. What you are expected to do

You are not expected to develop MIMOSA or write a model from scratch. For the core assignment, you should be able to:

1. load a set of model assumptions;
2. change a small number of documented settings;
3. run a simulation or optimization;
4. save every result with its parameter file;
5. compare scenarios using the dashboard or supplied plotting cells;
6. explain why the results differ;
7. test whether a policy remains effective under different assumptions.

Programming elegance is not assessed. A simple notebook with clear scenario names and well-explained comparisons is better than complicated code that group members do not understand.

## 2. Use the course environment

Use **[insert course Colab/Jupyter link]**. The environment will contain:

- the correct MIMOSA course version;
- a compatible optimization solver;
- required Python packages;
- prepared plotting and comparison functions;
- folders for model output and figures.

Do not spend assignment time repairing a private Python installation unless you have agreed this with an instructor. A notebook that works on one group member's computer but cannot be reproduced in the course environment is not sufficient.

Before beginning your project, run the environment-check cell supplied by the teaching team. Record the printed MIMOSA version in your `README`.

## 3. The standard imports

Most model-running notebooks begin with:

```python
from pathlib import Path

import pandas as pd

from mimosa import MIMOSA, load_params
```

Create a separate output folder for your group:

```python
GROUP_NAME = "replace_with_group_name"
OUTPUT_FOLDER = Path("output") / GROUP_NAME
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
```

Use short, descriptive scenario names such as:

```text
00_no_policy_no_adaptation
01_reference_joint_cba
02_mitigation_only
03_adaptation_only
10_low_climate_response
11_high_climate_response
20_joint_policy_low_realised_adaptation
```

Never reuse the same name for two different runs.

## 4. A helper for loading ACCREU settings

Start every scenario from a fresh call to `load_params()`. The helper below selects the ACCREU sectoral damage module and makes the main choices explicit.

```python
def accreu_params(
    adaptation="separate",
    monetise_mortality=False,
    end_year=2100,
):
    """Return a fresh parameter dictionary for one ACCREU scenario."""
    params = load_params()

    params["model structure"]["damage module"] = "ACCREU"
    params["model structure"]["damage module options"][
        "ACCREU adaptation"
    ] = adaptation
    params["model structure"]["damage module options"][
        "ACCREU_monetise_mortality"
    ] = monetise_mortality
    params["time"]["end"] = end_year

    return params
```

Valid adaptation settings are:

| Setting | Meaning |
|---|---|
| `"noadaptation"` | No explicit adaptation expenditure or avoided damages |
| `"combined"` | One combined adaptation decision for labour productivity and riverine flooding; sea-level-rise adaptation remains separate |
| `"separate"` | Separate adaptation decisions for labour productivity, riverine flooding, and sea-level rise |

For most student projects, use `end_year=2100` unless your research question requires longer-term sea-level-rise or capital effects. Longer runs take more time and place greater weight on assumptions beyond 2100.

## 5. Simulation and optimization

### 5.1 Simulation

In a simulation, you supply the policy controls and MIMOSA calculates their consequences.

```python
params = accreu_params(adaptation="noadaptation")
model = MIMOSA(params)

simulation = model.run_simulation(relative_abatement=0.25)
model.save_simulation(
    simulation,
    "constant_25_percent_abatement",
    folder=str(OUTPUT_FOLDER),
)
```

Here, `relative_abatement=0.25` applies 25% abatement in every modelled region and period after the initial period. This is useful for learning but is rarely a realistic final scenario.

Important simulation rules:

- ordinary optimization constraints are not automatically enforced;
- a carbon budget in `params` does not make a prescribed simulation comply with that budget;
- every control variable you omit is set to zero;
- a simulation evaluates a policy but does not determine whether it is optimal.

### 5.2 Optimization

In an optimization, MIMOSA chooses the control pathways according to the selected objective and constraints.

```python
params = accreu_params(adaptation="separate")
model = MIMOSA(params)

model.solve(verbose=False, ipopt_maxiter=10000)
model.save(
    "reference_joint_cba",
    folder=str(OUTPUT_FOLDER),
)
```

Before interpreting an optimization, write down:

- the objective;
- the welfare formulation;
- the discount rate;
- whether mortality is monetized;
- whether a carbon budget or temperature target is active;
- which adaptation representation is active;
- any constraints on negative emissions or mitigation speed.

An optimizer status of `ok` means that the solver completed successfully. It does not mean the assumptions are realistic or the result is a good policy recommendation.

## 6. The common reference scenarios

### 6.1 No policy and no adaptation

```python
params = accreu_params(adaptation="noadaptation")
model_no_policy = MIMOSA(params)

no_policy = model_no_policy.run_nopolicy_baseline()
model_no_policy.save_simulation(
    no_policy,
    "00_no_policy_no_adaptation",
    folder=str(OUTPUT_FOLDER),
)
```

`run_nopolicy_baseline()` sets all controls to zero and stores the damage reference used for avoided-damage calculations.

### 6.2 Mitigation only

```python
params = accreu_params(adaptation="noadaptation")
model_mitigation = MIMOSA(params)

model_mitigation.solve(verbose=False, ipopt_maxiter=10000)
model_mitigation.save(
    "02_mitigation_only",
    folder=str(OUTPUT_FOLDER),
)
```

Because the adaptation module is disabled, the optimizer can respond only through mitigation.

### 6.3 Adaptation only

For an adaptation-only simulation, keep mitigation at zero and calculate the analytically optimal adaptation level:

```python
params = accreu_params(adaptation="separate")
params["model structure"]["damage module options"][
    "ACCREU_adaptation_impose_optimal"
] = True

model_adaptation = MIMOSA(params)
adaptation_only = model_adaptation.run_nopolicy_baseline()
model_adaptation.save_simulation(
    adaptation_only,
    "03_adaptation_only",
    folder=str(OUTPUT_FOLDER),
)
```

This analytical setting is useful in simulation mode. It should not be confused with a jointly optimized mitigation-adaptation policy.

### 6.4 Joint mitigation and adaptation

```python
params = accreu_params(adaptation="separate")
model_joint = MIMOSA(params)

model_joint.solve(verbose=False, ipopt_maxiter=10000)
model_joint.save(
    "01_reference_joint_cba",
    folder=str(OUTPUT_FOLDER),
)
```

With separate adaptation, the policy controls are normally:

```text
relative_abatement
slr_adaptation_costs_abs
riverine_adaptation_costs_abs
labourprod_adaptation_costs_abs
```

You can inspect the controls for the selected model with:

```python
print(model_joint.simulator.control_variables)
```

## 7. Changing one set of assumptions

Always create a fresh parameter dictionary for every scenario.

### Climate response

```python
params = accreu_params()
params["temperature"]["TCRE"] = "0.82 delta_degC/(TtCO2)"
```

### Discounting

```python
params = accreu_params()
params["economics"]["PRTP"] = 0.01
```

`PRTP` is a fraction per year. A value of `0.01` means 1% per year.

### SSP baseline

```python
params = accreu_params()
params["SSP"] = "SSP3"
```

### Carbon budget

```python
params = accreu_params()
params["emissions"]["carbonbudget"] = "700 GtCO2"
```

### Mortality monetization

```python
params = accreu_params(monetise_mortality=True)
```

### Realized adaptation effectiveness

```python
params = accreu_params()
params["economics"]["damages"]["accreu"][
    "adaptation_effectiveness_scale_factor"
] = 0.5
```

This represents adaptation that is half as effective as assumed by the default effectiveness curves. It does not mean that adaptation expenditure is halved.

## 8. A genuine robustness test

Suppose a joint policy was designed assuming full adaptation effectiveness. To ask how that same policy performs when adaptation is less effective, copy every policy control into a newly configured model.

```python
# 1. Optimize the policy under the design assumptions.
design_params = accreu_params(adaptation="separate")
design_model = MIMOSA(design_params)
design_model.solve(verbose=False, ipopt_maxiter=10000)

# 2. Extract every control, not only mitigation.
control_values = {
    name: getattr(design_model.concrete_model, name).extract_values()
    for name in design_model.simulator.control_variables
}

# 3. Create a new model for the realized future.
realised_params = accreu_params(adaptation="separate")
realised_params["economics"]["damages"]["accreu"][
    "adaptation_effectiveness_scale_factor"
] = 0.5
realised_model = MIMOSA(realised_params)

# 4. Evaluate the original policy without re-optimizing it.
stressed_policy = realised_model.run_simulation(**control_values)
realised_model.save_simulation(
    stressed_policy,
    "20_joint_policy_low_realised_adaptation",
    folder=str(OUTPUT_FOLDER),
)
```

If you re-optimize after changing effectiveness, you are answering a different question: what policy would be chosen with advance knowledge of lower effectiveness? Both questions are useful, but they are not interchangeable.

## 9. Running a small scenario set

Loops are useful when one assumption takes several values. Keep the loop small and make every filename unique.

```python
for prtp in [0.005, 0.015, 0.03]:
    params = accreu_params(adaptation="separate")
    params["economics"]["PRTP"] = prtp

    model = MIMOSA(params)
    model.solve(verbose=False, ipopt_maxiter=10000)

    label = str(prtp).replace(".", "p")
    model.save(
        f"discount_rate_{label}",
        folder=str(OUTPUT_FOLDER),
    )
```

Joint ACCREU optimizations can take several minutes. First run one scenario interactively. Do not start a large loop shortly before a deadline. The teaching team may provide precomputed reference runs for expensive experiment sets.

## 10. Output files

Every saved scenario produces two files:

```text
scenario_name.csv
scenario_name.csv.params.json
```

The CSV contains model variables in a wide IAMC-like format:

| Variable | Region | Unit | 2025 | 2030 | ... | 2100 |
|---|---|---|---:|---:|---:|---:|

The JSON file contains the parameter settings, selected model modules, scenario type, and MIMOSA version. Always keep both files.

### Inspecting one variable in Python

```python
output = pd.read_csv(OUTPUT_FOLDER / "01_reference_joint_cba.csv")

temperature = output.loc[
    (output["Variable"] == "temperature")
    & (output["Region"] == "Global")
]

temperature
```

### Comparing regional values in 2100

```python
regional_damage_2100 = output.loc[
    output["Variable"] == "damage_costs",
    ["Region", "Unit", "2100"],
].sort_values("2100", ascending=False)

regional_damage_2100.head(10)
```

Use the MIMOSA dashboard or course plotting functions for most figures. Direct CSV inspection remains valuable for checking variable names, units, signs, and totals.

## 11. Useful variables

Availability depends on the selected modules.

### Climate and emissions

| Variable | Interpretation |
|---|---|
| `regional_emissions` | Regional CO2 emissions per year |
| `global_emissions` | Global CO2 emissions per year |
| `cumulative_emissions` | Cumulative global CO2 emissions |
| `relative_abatement` | Abatement relative to baseline emissions |
| `temperature` | Global warming above pre-industrial levels |
| `total_SLR` | Global mean sea-level rise |

### Costs, economy, and welfare

| Variable | Interpretation |
|---|---|
| `mitigation_costs` | Regional attributed mitigation expenditure |
| `domestic_mitigation_costs` | Cost of mitigation physically occurring in the region |
| `rel_mitigation_costs` | Mitigation costs relative to GDP |
| `carbonprice` | Regional marginal mitigation price |
| `GDP_gross` | GDP before current-period climate and mitigation costs |
| `GDP_net` | GDP after represented costs |
| `consumption` | Regional consumption used in welfare calculations |
| `GDP_loss` | Total GDP loss relative to the SSP baseline |
| `utility` | Regional utility or consumption measure, depending on the welfare module |
| `NPV` | Discounted objective accumulation |

### ACCREU impacts and adaptation

| Variable family | Interpretation |
|---|---|
| `*_damage_costs_gross` | Sectoral damages before adaptation |
| `*_adaptation_costs_abs` | Absolute adaptation expenditure |
| `*_adaptation_costs` | Adaptation expenditure relative to GDP |
| `*_avoided_damages_adapt` | Fraction of gross damages avoided through adaptation |
| `*_damage_costs_residual` | Damages remaining after adaptation |
| `*_damage_costs` | Residual damages plus adaptation cost for the sector |
| `mortality_heat_related` | Change in heat-related mortality relative to the initial climate |
| `mortality_cold_related` | Change in cold-related mortality; negative values can represent avoided cold deaths |
| `market_and_non_market_damage_costs` | Combined monetized market and non-market damages when mortality is monetized |

The prefix is normally `labourprod`, `riverine`, or `slr`. Under combined adaptation, labour-productivity and riverine adaptation variables are replaced by a `combined_labprod_riv` family.

## 12. Essential checks before interpreting results

### Check 1: solver completion

```python
print(model.status)
```

Do not use an optimization result if the solver failed or stopped without an acceptable solution. Save the warning and ask an instructor.

### Check 2: units

Never compare a fraction of GDP directly with an absolute cost. Check the `Unit` column. A value of `0.01` in a `fraction_of_GDP` variable means 1% of GDP, not 0.01%.

### Check 3: sectoral accounting

Where adaptation is active, check conceptually that:

```text
sector total cost = residual sector damage + adaptation cost
```

and that residual damage is smaller than gross damage when avoided damages are positive.

### Check 4: physical versus attributed mitigation

With emissions trading, `regional_emission_reduction` shows where mitigation occurs, while `attributed_emission_reductions` shows to whom it is assigned. Similarly, domestic and attributed mitigation costs can differ.

### Check 5: mortality signs

Cold-related mortality changes can be negative. Do not call these "negative deaths"; interpret them as avoided deaths relative to the initial-climate reference.

### Check 6: scenario logic

Before looking at exact values, state the expected ordering. For example, lower realized adaptation effectiveness should normally increase residual damages for a fixed policy. If it does not, investigate the mechanism and settings.

## 13. Frequent mistakes

- Changing `params` after constructing `MIMOSA(params)`. This does not update the existing model.
- Reusing a modified parameter dictionary for another scenario.
- Reusing a filename and overwriting an earlier result.
- Calling a prescribed simulation "optimal."
- Assuming a simulation obeys a carbon-budget constraint.
- Copying only `relative_abatement` when replaying a model with adaptation controls.
- Comparing results from different SSPs without recognizing that population, GDP, and baseline emissions all changed.
- Treating mortality valuation, discounting, or inequality aversion as technical rather than normative assumptions.
- Reporting only 2100 and missing the timing of costs, learning, adaptation, or damages.
- Interpreting a regional average as applying equally to every person in that region.
- Editing CSV results manually instead of correcting the analysis code.

## 14. Troubleshooting

### `KeyError` when changing a setting

Check that you are using the course branch and that every dictionary level is spelled exactly as in the example. Print the relevant section:

```python
params = load_params()
print(params["model structure"])
```

### Solver failure or infeasible model

1. Confirm that the reference scenario runs.
2. Undo the most recent parameter change.
3. Check units and bounds.
4. Shorten the model horizon for diagnosis, not for final interpretation.
5. Do not keep increasing the iteration limit without understanding the problem.
6. Record the full error and settings and ask an instructor.

### A run takes a long time

Separate sectoral adaptation adds many decision variables. Avoid unnecessary long horizons and large parameter grids. Use precomputed instructor runs when supplied.

### Different group members obtain different results

Compare:

- MIMOSA version;
- complete `.params.json` files;
- scenario type;
- notebook execution order;
- solver status;
- output filenames and timestamps.

## 15. Reproducibility checklist

- [ ] Every scenario starts from a fresh `load_params()` call.
- [ ] Every scenario has a unique and meaningful name.
- [ ] CSV and `.params.json` files are stored together.
- [ ] Failed runs and changes to the proposal are recorded.
- [ ] Every main figure can be traced to specific output files.
- [ ] The notebook runs from top to bottom in the course environment.
- [ ] The `README` identifies the model version and scenario order.
- [ ] Every group member can explain the main settings and comparisons.

## 16. Further documentation

Use the full MIMOSA documentation when you need the scientific equations, complete parameter reference, or developer API:

- [MIMOSA documentation](https://utrechtuniversity.github.io/mimosa/)
- [Running MIMOSA](https://utrechtuniversity.github.io/mimosa/run/)
- [Simulation and optimization](https://utrechtuniversity.github.io/mimosa/run/simulation/)
- [Changing parameters](https://utrechtuniversity.github.io/mimosa/run/changingparams/)
- [Model components](https://utrechtuniversity.github.io/mimosa/components/)

For assignment-specific decisions, the course guide and course notebook take precedence.

