# Units

MIMOSA uses units to keep input values, model variables and exported results interpretable. When
adding a variable or parameter, first decide whether it represents a stock, an annual flow, a ratio
or a dimensionless value. Then give it the corresponding unit.

## Standard model units

The common unit names are defined centrally in
[`default_units.yaml`]({{config.repo_url}}/blob/master/mimosa/inputdata/config/default_units.yaml):

| Unit name | Default unit | Used for |
| --- | --- | --- |
| `currency_unit` | trillion USD2010/yr | GDP and annual costs |
| `emissions_unit` | GtCO2 | Cumulative emissions and carbon budgets |
| `emissionsrate_unit` | GtCO2/yr | Annual emissions and emission reductions |
| `temperature_unit` | delta_degC | Temperature relative to pre-industrial levels |
| `population_unit` | billion | Population |

Use these names when a new quantity should follow MIMOSA's standard scale. Compound units can be
created with multiplication, division and parentheses, for example
`currency_unit / emissionsrate_unit` for a carbon price.

Physical units can also be used directly when there is no standard MIMOSA name. Sea-level rise, for
example, is expressed using `m`.

!!! note "Stocks and annual flows are different"

    `emissions_unit` represents an amount of emissions, while `emissionsrate_unit` represents an
    amount per year. A cumulative-emissions equation therefore multiplies an emissions flow by the
    timestep length:

    $$
    \text{cumulative emissions}_t =
    \text{cumulative emissions}_{t-1}
    + \Delta t \cdot \text{emissions flow}_t.
    $$

    The same distinction applies to economic quantities: MIMOSA's `currency_unit` is an annual
    flow, as used for GDP and yearly costs.

## Adding units to variables and parameters

Import `quant` from `mimosa.common` and use `quant.unit(...)` in the Pyomo definition:

```python
from mimosa.common import AbstractModel, Param, Var, quant


def get_constraints(m: AbstractModel, context):
    m.adaptation_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
    )
    m.maximum_adaptation = Param(
        units=quant.unit("dimensionless"),
        doc="::economics.adaptation.maximum",
    )

    # ... equations and constraints ...
```

Common examples are:

```python
quant.unit("emissions_unit")
quant.unit("emissionsrate_unit")
quant.unit("currency_unit / emissionsrate_unit")
quant.unit("fraction_of_GDP")
quant.unit("dimensionless")
```

The units attached to variables and time-dependent parameters are included in the `Unit` column of
exported MIMOSA results.

!!! warning "Unit metadata does not repair an incorrectly scaled equation"

    All terms that are added or equated should describe compatible quantities. Pay particular
    attention to factors of $\Delta t$, percentages versus fractions, and millions versus billions.
    Sensible model units also keep numerical values near a manageable scale for the optimiser.

## Configuration parameters with units

Use the `quantity` parameter type when a configurable value has a physical unit. Define both the
target `unit` and a default value that includes a unit:

```yaml title="mimosa/inputdata/config/config_default.yaml"
economics:
  adaptation:
    maximum_annual_cost:
      descr: Maximum annual adaptation expenditure
      type: quantity
      unit: currency_unit
      default: 0.1 trillion USD2010/yr
```

Link this configuration value to a Pyomo parameter in the usual way:

```python
m.maximum_annual_adaptation_cost = Param(
    doc="::economics.adaptation.maximum_annual_cost",
    units=quant.unit("currency_unit"),
)
```

Users can provide any compatible unit:

```python
from mimosa import load_params

params = load_params()
params["economics"]["adaptation"]["maximum_annual_cost"] = "100 billion USD2010/yr"
```

When the model is created, MIMOSA converts this value to the target `currency_unit`. An incompatible
value, such as a temperature supplied for a cost parameter, produces a configuration error. A bare
number should only be used for a `float` parameter when the value is genuinely dimensionless.

For optional quantities such as the carbon budget, `can_be_false: true` allows the corresponding
constraint or setting to be disabled with `False`. See [Adding parameters and
data](parameters.md#config-params) for the full configuration workflow.

## Converting quantities directly

`quant(...)` can also convert a value explicitly. By default it returns only the numerical magnitude
in the requested target unit:

```python
from mimosa.common import quant

budget = quant("5000 MtCO2", "emissions_unit")
# budget == 5.0, expressed in the default emissions_unit (GtCO2)

emissions = quant(5000, "MtCO2/yr", "emissionsrate_unit")
# emissions == 5.0, expressed in GtCO2/yr
```

Most component parameters do not need to call `quant(...)` themselves: values declared as
`type: quantity` are converted while the model is instantiated.

## Units in input files

Time- and region-dependent input data use the `unit` column in the IAMC-formatted source file. The
target unit is selected in `config_default.yaml`:

```yaml title="mimosa/inputdata/config/config_default.yaml"
input:
  variables:
    emissions:
      type: datasource
      default:
        variable: Emissions|CO2
        unit: emissionsrate_unit
        scenario: "{SSP}-Baseline"
        model: IMAGE 3.4
        file: inputdata/data/data_IMAGE_SSP_updated.csv
```

MIMOSA reads the source unit and converts the values to `emissionsrate_unit` before interpolation.
For example, input in MtCO2/yr is converted to the default GtCO2/yr.

Regional parameter CSV files do not contain unit metadata and are not converted automatically. Their
numerical values must already use the unit declared on the corresponding `Param`. Document that unit
in the component explanation or beside the column definition so that future data updates use the same
scale.

## Checklist for a new quantity

Before adding a new variable or parameter, check that:

1. it is clear whether the quantity is a stock, annual flow, ratio or dimensionless value;
2. its `Var` or `Param` has an appropriate `units=quant.unit(...)` declaration;
3. every equation combines compatible quantities;
4. configurable dimensional values use `type: quantity` and include a unit;
5. input data are converted to the same target unit, or regional CSV values are already in that unit;
6. the unit and interpretation are stated in the component documentation.
