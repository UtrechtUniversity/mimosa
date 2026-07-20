---
title: "Scaffolding MIMOSA Extensions for Assignment 4"
audience: "Instructors, teaching assistants, and advanced student groups"
status: "Technical design draft"
model_version: "feat_accreu_adaptation_sectoral_damages"
---

# Scaffolding MIMOSA Extensions for Assignment 4

## Agriculture, biodiversity, and mortality valuation without turning the assignment into a programming course

## 1. Is the existing MIMOSA documentation enough?

The existing MIMOSA documentation is sufficient for an experienced Python modeller to learn how to:

- create variables and equations;
- add configuration parameters and regional data;
- register fixed or selectable components;
- work with units;
- run simulation and optimization tests.

It is not sufficient as the only support for this assignment. Students would still need to decide where a new impact enters GDP or welfare, how to avoid double-counting, how to create regional data files, how to register a component, and how to diagnose Pyomo or solver errors. Those tasks are valuable for model developers but would distract most students from the intended scientific questions.

The recommended division of work is:

### Teaching team prepares

- package and file structure;
- imports and component registration;
- configuration schema;
- unit declarations;
- regional parameter loading;
- aggregation into market damages, non-market damages, or constraints;
- output and plotting functions;
- automated tests and reference runs;
- clearly marked student-editable functions.

### Students decide or complete

- the substantive response equation;
- a small set of parameter values or alternative calibrations;
- whether a representation is conceptually defensible;
- scenario comparisons;
- validation expectations;
- interpretation and limitations.

This keeps the extension scientifically demanding while making coding difficulty manageable.

## 2. Target architecture

This guide targets the course branch based on:

```text
feat_accreu_adaptation_sectoral_damages
```

In that branch, the ACCREU damage package contains separate modules for:

```text
mimosa/components/damages/accreu/
|-- all_damages.py
|-- labour_productivity.py
|-- riverine_flooding.py
|-- sealevelrise.py
|-- mortality.py
|-- combined_nslr_adaptation.py
`-- utils.py
```

`all_damages.py` constructs the sector modules and aggregates them into:

- `damage_costs`: market damage and adaptation costs as a fraction of GDP;
- `damage_costs_abs`: the corresponding absolute market cost;
- `non_market_damage_costs_abs`: monetized mortality in the current implementation;
- `market_and_non_market_damage_costs_abs`: combined reporting;
- `market_and_non_market_damage_costs`: combined reporting relative to GDP.

The Cobb-Douglas component subtracts market damages and mitigation costs in `GDP_net`, while non-market damages are subtracted from consumption. An extension must therefore state explicitly whether it affects:

1. a reported physical indicator only;
2. market production or GDP;
3. consumption or non-market welfare;
4. an optimization constraint or guardrail;
5. a new decision variable and its costs.

Do not add an outcome to the objective merely because it can be expressed in dollars.

## 3. Recommended course-extension structure

For a controlled course distribution, add a subpackage inside the ACCREU damage package:

```text
mimosa/components/damages/accreu/course_extensions/
|-- __init__.py
|-- agriculture.py
|-- biodiversity.py
`-- valuation.py
```

Import and construct the enabled modules near the beginning of `all_damages.py`, before total damages are aggregated.

The relevant options can live under `damage module options`:

```yaml
model structure:
  damage module options:
    course agriculture:
      descr: Include the course agriculture extension
      type: bool
      default: false

    course biodiversity representation:
      descr: How biodiversity enters the analysis
      type: enum
      values:
        - indicator_only
        - nonuse_value
        - ecosystem_service
        - guardrail
      default: indicator_only

    course mortality valuation:
      descr: How mortality risk is valued
      type: enum
      values:
        - physical_only
        - equal_global_vsl
        - income_scaled_vsl
      default: physical_only
```

The exact names can change, but stable names are important because every scenario saves them in its parameter file.

## 4. Four levels of extension difficulty

### Level 1: output-only indicator

The new variable is calculated and exported but does not affect GDP, consumption, welfare, or policy constraints.

Examples:

- climate-related crop-yield loss;
- food-security pressure;
- biodiversity condition;
- population exposed above a threshold.

This is the safest student-editable extension. It works in simulation and optimization but does not change the optimized pathway.

### Level 2: additional damage or welfare term

The indicator is translated into:

- an additional market-damage fraction; or
- an absolute non-market welfare cost.

This can change optimal mitigation and adaptation. Calibration, welfare interpretation, and double-counting become central.

### Level 3: guardrail or policy constraint

The indicator remains non-monetary, but the optimizer must respect a threshold.

Examples:

- maximum food-insecurity pressure;
- minimum biodiversity condition;
- maximum mortality increase.

General constraints affect optimization only. A simulation can violate them, so compliance must be checked separately.

### Level 4: new decision and feedback

The extension adds a control such as agricultural adaptation, ecosystem restoration, or public-health protection.

This is appropriate only for a heavily prewired advanced template. It changes degrees of freedom, simulation controls, cost accounting, and solver behaviour.

## 5. Agriculture extension

### 5.1 Scientific distinction to preserve

Keep the following quantities separate:

1. crop yield or agricultural output;
2. agricultural value added;
3. food prices;
4. food consumption or calorie availability;
5. food insecurity or welfare;
6. economy-wide GDP.

A 10% yield loss is not automatically a 10% loss of agricultural value added, and neither is automatically a 10% loss of food consumption. Trade, substitution, prices, producer income, consumer expenditure, and adaptation mediate the relationship.

The course module should therefore expose the translation step rather than hiding it.

### 5.2 Suggested outputs

Use stable names such as:

| Variable | Unit | Role |
|---|---|---|
| `agriculture_yield_loss` | fraction | Physical or biophysical indicator |
| `agriculture_market_damage_costs` | fraction of GDP | Direct market-damage approximation |
| `food_price_pressure` | fraction | Stylized price response |
| `food_security_pressure` | dimensionless index | Non-monetary distributional outcome |
| `agriculture_non_market_costs_abs` | currency per year | Optional monetized welfare term |

Do not require all representations in every scenario. The research question can compare them.

### 5.3 Instructor-prepared regional parameters

Add reviewed course columns to a regional CSV, for example:

```text
region
agriculture_gdp_share
agriculture_yield_linear
agriculture_yield_quadratic
food_expenditure_share
food_supply_elasticity
food_demand_elasticity
food_security_vulnerability
```

Document whether each value is:

- a fraction or percentage;
- calibrated to a specific year;
- PPP- or market-exchange-rate based;
- regional or global;
- empirical, literature-derived, or deliberately illustrative.

Students should not be asked to invent 26 regional coefficients without data.

### 5.4 Minimal agriculture component

The following template illustrates an output and GDP-damage layer. It is not a complete food-system model.

```python
from mimosa.common import (
    AbstractModel,
    ModelContext,
    Param,
    RegionalEquation,
    Var,
    quant,
)


def get_constraints(m: AbstractModel, context: ModelContext):
    """Course agriculture extension with a transparent reduced-form response."""

    # Regional parameters are loaded from the instructor-prepared course CSV.
    m.agriculture_gdp_share = Param(
        m.regions,
        doc="regional::COURSE.agriculture_gdp_share",
    )
    m.agriculture_yield_linear = Param(
        m.regions,
        doc="regional::COURSE.agriculture_yield_linear",
    )
    m.agriculture_yield_quadratic = Param(
        m.regions,
        doc="regional::COURSE.agriculture_yield_quadratic",
    )
    m.food_security_vulnerability = Param(
        m.regions,
        doc="regional::COURSE.food_security_vulnerability",
    )

    m.agriculture_yield_loss = Var(
        m.t,
        m.regions,
        bounds=(-0.5, 0.9),
        units=quant.unit("dimensionless"),
    )
    m.agriculture_market_damage_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
    )
    m.food_security_pressure = Var(
        m.t,
        m.regions,
        units=quant.unit("dimensionless"),
    )

    def yield_loss(m, t, r):
        # STUDENT-EDITABLE EQUATION
        warming = m.temperature[t] - m.temperature[0]
        return (
            m.agriculture_yield_linear[r] * warming
            + m.agriculture_yield_quadratic[r] * warming**2
        )

    return [
        RegionalEquation(m.agriculture_yield_loss, yield_loss),
        RegionalEquation(
            m.agriculture_market_damage_costs,
            lambda m, t, r: (
                m.agriculture_gdp_share[r]
                * m.agriculture_yield_loss[t, r]
            ),
        ),
        RegionalEquation(
            m.food_security_pressure,
            lambda m, t, r: (
                m.food_security_vulnerability[r]
                * m.agriculture_yield_loss[t, r]
            ),
        ),
    ]
```

The teaching team should decide whether negative yield loss represents a benefit and whether bounds should be active. Python `max()` and `min()` cannot be used on Pyomo variables. Use MIMOSA's smooth helper functions if a differentiable lower or upper bound is required.

### 5.5 Connecting agriculture to the economy

For the GDP-only representation, instructors can add the agriculture market term to the ACCREU market-damage aggregation:

```python
base_market_damage = (
    m.labourprod_damage_costs[t, r]
    + m.riverine_damage_costs[t, r]
    + m.slr_damage_costs[t, r]
)

return base_market_damage + m.agriculture_market_damage_costs[t, r]
```

Do not ask students to edit this aggregation. Provide a model option that turns the term on or off.

For an indicator-only representation, calculate and export `agriculture_yield_loss` and `food_security_pressure` but do not add either to `damage_costs`.

For a non-market food-security penalty, create a separate absolute cost and aggregate it with other non-market costs before consumption is calculated. The units and welfare interpretation require more care than the GDP-only case.

### 5.6 Agriculture validity checks

At minimum, test that:

- yield loss is zero in the initial period;
- warmer test cases produce the expected sign;
- a zero agricultural GDP share produces zero market damage;
- the GDP-only damage equals agricultural share times yield loss;
- food-security pressure can differ strongly between regions with equal yield loss;
- turning the objective coupling off leaves the optimized pathway unchanged;
- turning it on changes results only through the documented aggregation;
- market agriculture damages are not already present elsewhere in the chosen damage module.

## 6. Biodiversity and ecosystems extension

### 6.1 Choose what is being represented

Do not name a generic variable `biodiversity` without defining it. Possible meanings include:

- species richness;
- mean species abundance;
- potentially disappeared fraction;
- ecosystem intactness;
- extinction risk;
- natural-capital stock;
- an ecosystem-service index.

The course module should use a neutral name such as `biodiversity_condition_index` until a specific empirical metric is selected.

It must also be labelled as **climate-related biodiversity pressure**, because MIMOSA does not represent all major biodiversity drivers.

### 6.2 Simple bounded response

For a first course version, use a smooth temperature-dependent response rather than a full ecological stock model:

```python
from mimosa.common import (
    AbstractModel,
    ModelContext,
    Param,
    RegionalEquation,
    Var,
    exp,
    quant,
    soft_min,
)


def get_constraints(m: AbstractModel, context: ModelContext):
    m.biodiversity_max_loss = Param(
        m.regions,
        doc="regional::COURSE.biodiversity_max_loss",
    )
    m.biodiversity_temperature_sensitivity = Param(
        m.regions,
        doc="regional::COURSE.biodiversity_temperature_sensitivity",
    )
    m.biodiversity_temperature_threshold = Param(
        m.regions,
        doc="regional::COURSE.biodiversity_temperature_threshold",
    )

    m.biodiversity_loss = Var(
        m.t,
        m.regions,
        bounds=(0, 1),
        units=quant.unit("dimensionless"),
    )
    m.biodiversity_condition_index = Var(
        m.t,
        m.regions,
        bounds=(0, 1),
        units=quant.unit("dimensionless"),
    )

    def loss_response(m, t, r):
        # STUDENT-EDITABLE RESPONSE OR PARAMETERIZATION
        above_threshold = soft_min(
            m.temperature[t] - m.biodiversity_temperature_threshold[r],
            scale=1,
        )
        return m.biodiversity_max_loss[r] * (
            1
            - exp(
                -m.biodiversity_temperature_sensitivity[r]
                * above_threshold
            )
        )

    return [
        RegionalEquation(m.biodiversity_loss, loss_response),
        RegionalEquation(
            m.biodiversity_condition_index,
            lambda m, t, r: 1 - m.biodiversity_loss[t, r],
        ),
    ]
```

This formulation is deliberately reduced-form. It has no explicit ecological recovery, species interactions, land-use effects, or local climate. Its transparency makes it suitable for comparing decision representations.

### 6.3 Alternative decision representations

#### Indicator only

Export the biodiversity variables without adding them to damages or constraints. The optimized policy will ignore biodiversity, which is an important result rather than a software error.

#### Non-use value

Create an absolute non-market cost:

```python
m.biodiversity_nonuse_costs_abs = Var(
    m.t,
    m.regions,
    units=quant.unit("currency_unit"),
)

RegionalEquation(
    m.biodiversity_nonuse_costs_abs,
    lambda m, t, r: (
        m.biodiversity_value_share[r]
        * m.biodiversity_loss[t, r]
        * m.GDP_gross[t, r]
    ),
)
```

This is a willingness-to-pay or consumption-equivalent representation. It is not the intrinsic value of nature. Scaling it with GDP embeds income differences in the valuation.

#### Ecosystem-service damage

Translate biodiversity condition into a specific service before adding a market cost. For example, an agriculture-related pollination effect should normally enter the agriculture module, not an unexplained general GDP damage.

This route has the greatest risk of double-counting because flooding, food, health, or productivity may already be represented elsewhere.

#### Ecological guardrail

Use an optimization constraint:

```python
from mimosa.common import RegionalConstraint

RegionalConstraint(
    lambda m, t, r: (
        m.biodiversity_condition_index[t, r]
        >= m.minimum_biodiversity_condition[r]
    ),
    name="course_biodiversity_guardrail",
)
```

The guardrail must be scientifically and normatively justified. It is not enforced in simulation mode.

### 6.4 Advanced natural-capital stock

A dynamic stock could follow:

```text
condition[t]
= condition[t-1]
+ recovery[t-1] * dt
- climate_loss[t-1] * dt
```

This creates path dependence and can represent slow recovery or irreversibility. It also creates more opportunities for infeasible values, numerical problems, and unsupported calibration. Use it only after the static response module is working and tested.

### 6.5 Biodiversity validity checks

- The metric and reference state are explicitly defined.
- Initial condition and loss remain within the intended range.
- A zero sensitivity produces no climate-related loss.
- The response is monotonic or non-monotonic exactly as justified.
- Indicator-only mode does not change the optimized policy.
- Non-use valuation changes consumption only through the documented channel.
- A guardrail is checked explicitly in every optimization output.
- Climate-only biodiversity pressure is not labelled total biodiversity loss.
- Ecosystem-service terms do not duplicate agriculture, flooding, or other ACCREU damages.

## 7. Mortality valuation extension

### 7.1 Current ACCREU behaviour

The ACCREU branch calculates regional heat- and cold-related changes in mortality. When monetization is active, it calculates a regional VSL proportional to GDP per capita and subtracts the resulting non-market cost from consumption.

This provides a useful starting point but should be made selectable for the assignment.

### 7.2 Recommended valuation options

| Option | Physical results | Enters objective | Main interpretation |
|---|---:|---:|---|
| `physical_only` | Yes | No | Multi-metric reporting; mortality has no weight in single-objective optimization |
| `equal_global_vsl` | Yes | Yes | Equal dollar valuation of a statistical mortality-risk change across regions |
| `income_scaled_vsl` | Yes | Yes | Conventional income-related willingness-to-pay transfer; different dollar values across regions |

The teaching team should refactor the mortality component so `all_damages.py` passes a valuation option rather than a single Boolean.

### 7.3 Equal global VSL

Add a configuration parameter with an explicit unit:

```yaml
economics:
  damages:
    accreu:
      global_vsl:
        descr: Equal global value of a statistical life for course scenarios
        type: quantity
        unit: currency_unit/population_unit
        default: "[insert reviewed value and unit]"
```

Then define:

```python
m.mortality_vsl_global = Param(
    doc="::economics.damages.accreu.global_vsl",
    units=quant.unit("currency_unit/population_unit"),
)

RegionalEquation(
    m.mortality_damage_costs_abs,
    lambda m, t, r: (
        m.mortality_vsl_global
        * (
            m.mortality_heat_related[t, r]
            + m.mortality_cold_related[t, r]
        )
    ),
)
```

The unit conversion must match the mortality variable's population scale. Test this explicitly; billion people multiplied by a value per person can easily introduce a factor-of-one-billion error if course units are misunderstood.

### 7.4 Income-scaled VSL

The existing branch calculates VSL as a multiple of regional GDP per capita. Retain the multiplier as a documented scenario assumption. Clarify whether the same income elasticity applies across space and time.

For teaching, show both the physical mortality and the resulting regional VSL. Students should be able to see that a common risk change receives different monetary weights.

### 7.5 VOLY is not a scalar replacement

Do not implement VOLY by simply dividing the current VSL by an assumed remaining lifetime. A defensible VOLY pathway needs:

- mortality changes by age group;
- regional life expectancy or life tables;
- years of life lost;
- a rule for valuing and discounting future life years;
- consistent population projections.

Until these data and dimensions are added, VOLY should remain an advanced conceptual comparison or a separately prepared extension.

### 7.6 Mortality validity checks

- Heat and cold mortality changes are reported separately.
- Negative cold mortality is labelled avoided mortality, not negative deaths.
- Physical mortality results are identical across valuation options.
- `physical_only` does not alter consumption.
- Equal VSL gives the same value per statistical death in every region.
- Income-scaled VSL changes predictably with GDP per capita.
- Units are tested with a hand-calculated one-region example.
- Mortality is not already included in another damage aggregate.

## 8. Aggregation and double-counting

Before connecting a new term to welfare, complete this table:

| New variable | Physical phenomenon | Existing MIMOSA variable that may overlap | Market or non-market | Added to GDP, consumption, constraint, or output only? |
|---|---|---|---|---|
| | | | | |

Common double-counting risks include:

- agricultural productivity already embedded in an aggregate CGE damage function;
- pollination counted as both biodiversity damage and agricultural loss;
- flood protection counted as ecosystem-service loss and riverine or coastal damage;
- heat mortality counted in both mortality and labour productivity;
- adaptation expenditure counted once as a sector cost and again as a generic investment cost;
- non-use biodiversity value presented as if it were also an ecosystem-service value.

If overlap cannot be ruled out, keep the extension as an output-only indicator and discuss the consequences rather than adding it to total damages.

## 9. Making student editing safe

### Use explicit markers

```python
# =============================
# STUDENT-EDITABLE SECTION START
# =============================

def response_function(m, t, r):
    # Replace this line with the prepared response equation.
    raise NotImplementedError

# ===========================
# STUDENT-EDITABLE SECTION END
# ===========================
```

### Provide named alternatives

Students can select from functions rather than edit package registration:

```python
RESPONSE_FUNCTIONS = {
    "linear": response_linear,
    "quadratic": response_quadratic,
    "threshold": response_threshold,
}
```

### Validate parameters early

Provide notebook assertions such as:

```python
assert 0 <= agriculture_gdp_share <= 1
assert food_expenditure_share >= 0
assert biodiversity_max_loss <= 1
assert adaptation_effectiveness_scale_factor <= 1
```

For regional tables, report the regions and columns containing missing or out-of-range values before model construction.

### Separate scientific choices from plumbing

Students should not need to modify:

- `abstract_model.py`;
- `all_damages.py` aggregation;
- `cobbdouglas.py`;
- unit configuration;
- data-loading code;
- solver settings;
- output exporters.

## 10. Testing strategy for instructors

### 10.1 Construction tests

For every extension option, verify that:

```python
model = MIMOSA(params, prerun=False)
```

constructs successfully and creates the expected variables.

### 10.2 Simulation tests

Check:

- initial values;
- signs and ranges;
- equation identities;
- regional dimensions;
- results under zero and high test parameters;
- dependency ordering without circular same-period equations.

### 10.3 Optimization smoke tests

Use a short horizon first:

```python
params["time"]["end"] = 2050
```

Confirm solver success for every course option. Then test the final 2100 configurations supplied to students.

### 10.4 Scientific regression tests

Save a small reviewed reference table containing values such as:

- temperature in 2100;
- global emissions in 2050;
- global and selected regional damage shares;
- sectoral adaptation spending;
- physical mortality;
- agriculture and biodiversity indicators.

Tests should use tolerances and detect unintended changes when the course branch is updated.

### 10.5 Assignment-level tests

Run the exact notebook students receive from top to bottom in a clean environment. Verify:

- every reference output is created;
- cached results load correctly;
- filenames are unique;
- figures have correct labels and units;
- expensive cells are marked;
- error messages tell students what to do next.

## 11. Suggested scaffold packages

To accommodate different experience levels, provide three packages.

### Package A: analysis only

- All model code is fixed.
- Students choose scenarios and interpret results.
- Appropriate for every topic.

### Package B: equation completion

- File and variables are complete.
- Students fill one response equation and choose parameters.
- A test cell immediately checks values and model construction.
- Recommended for agriculture and biodiversity groups.

### Package C: advanced module

- Students may add a parameter, state variable, or decision equation.
- Registration and aggregation remain instructor controlled.
- Requires approval and a short verification plan.

Grades should be based on scientific quality, not package level.

## 12. Release checklist for the course branch

- [ ] ACCREU reference scenarios solve in the final environment.
- [ ] Student-facing parameter names match the notebook and guide.
- [ ] Agriculture and biodiversity can be enabled independently.
- [ ] Indicator-only options do not change optimization results.
- [ ] Market and non-market aggregation is documented and tested.
- [ ] Equal and income-scaled mortality valuation both work.
- [ ] Units are visible in exported output.
- [ ] No extension duplicates an existing damage channel without an explicit warning.
- [ ] The 2100 reference run time is acceptable or results are cached.
- [ ] All student-editable sections have tests and reset instructions.
- [ ] A clean course notebook reproduces every example in the student guide.
- [ ] Stable reference outputs are archived for instructors.

## 13. Relationship to the main MIMOSA documentation

Use this guide for course architecture and scaffolding decisions. Use the main MIMOSA developer documentation for the underlying API:

- [Extending MIMOSA](https://utrechtuniversity.github.io/mimosa/extending/)
- [Creating components](https://utrechtuniversity.github.io/mimosa/extending/components/)
- [Variables, equations, and constraints](https://utrechtuniversity.github.io/mimosa/extending/variables_constraints/)
- [Parameters and regional data](https://utrechtuniversity.github.io/mimosa/extending/parameters/)
- [Units](https://utrechtuniversity.github.io/mimosa/extending/units/)
- [Selectable modules](https://utrechtuniversity.github.io/mimosa/extending/selectable_modules/)
- [Model options](https://utrechtuniversity.github.io/mimosa/extending/model_options/)

The main documentation explains how the software works. This course guide explains which parts should be exposed to students and which should remain instructor-controlled.
