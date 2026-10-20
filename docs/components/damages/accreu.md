---
icon: material/gamepad-circle
variable_context: accreu_sectoral
---

[:octicons-arrow-left-24: Back to damage models](index.md)

During the ACCREU project, new damage estimates were developed for [:material-home-flood: riverine flooding](accreu.md#riverine-flooding), [:material-human-male-male: labour productivity](accreu.md#labour-productivity),
[:material-waves-arrow-up: sea-level rise](accreu.md#sea-level-rise) and [:material-heart-pulse: mortality](accreu.md#mortality). Moreover, adaptation costs and effectiveness were estimated for all sectors
(except mortality).

Usage:

=== "Damages only"

    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    model = MIMOSA(params)
    ```

=== "Damages and adaptation"

    ```python hl_lines="2-3"
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"
    model = MIMOSA(params)
    ```

By default, only the damages are considered, without adaptation. Adaptation can be enabled with the parameter [ACCREU adaptation](#param__economics.damages.accreu.adaptation) set to `sectoral`. If adaptation is enabled, the regional adaptation costs for each sector become additional control variables (either optimised by the solver, or set by the user in simulation mode). The adaptation costs are then used to reduce the damages in sector $i$ according to the adaptation level:

$$
\text{damages}_{i,t,r} = \text{gross damages}_{i,t,r} \cdot (1 - \text{adapt. level}_{i,t,r}),
$$

:::mimosa.components.damages.accreu.utils.adaptation_effectiveness_fct

## Impact sectors

=== ":material-home-flood: Riverine flooding"

    :::mimosa.components.damages.accreu.riverine_flooding.get_constraints

=== ":material-human-male-male: Labour productivity"

    :::mimosa.components.damages.accreu.labour_productivity.get_constraints

=== ":material-waves-arrow-up: Sea level rise"

    :::mimosa.components.damages.accreu.sealevelrise.get_constraints

=== ":material-heart-pulse: Mortality"

    :::mimosa.components.damages.accreu.mortality.get_constraints

## Total damages and adaptation

:::mimosa.components.damages.accreu.all_damages.get_constraints

## Advanced options

### Choosing adaptation expenditure

=== "Solver-controlled adaptation"

    - Meaning of `solver_control`.
    - Adaptation controls and optimisation goal.
    - Expenditure bounds.

=== "Analytical adaptation"

    - Meaning of `analytical_optimum`.
    - Local optimum equation and interpretation.
    - Difference from a full intertemporal welfare optimum.
    - **Graph:** residual damages plus expenditure for a selected impact, showing its local analytical optimum.

### Optimisation strategy

=== "Mitigation then adaptation"

    - Order of the mitigation optimisation and adaptation calculation.
    - Required settings and restrictions.
    - Reasons for differences from the joint workflow.

=== "Joint CBA"

    - Mitigation and adaptation choices in the joint workflow.
    - Solver-controlled and analytical adaptation variants.

### Extra options

- Table of options, configuration paths, allowed values and effects.
- Links to the [parameter reference](../../parameters.md) for defaults and types.
- Effectiveness scaling and delayed adaptation.
- Related mortality monetisation and valuation settings.

### Calibration

=== "Original calibration"

    - Source-model coefficients and interpretation of `accreu`.
    - Coefficient provenance and regional variation.

=== "Literature calibrations"

    - Low, central and high calibration choices.
    - Changes to effectiveness and expenditure coefficients.
    - Distinction between calibration targets and uncertainty.
    - Evidence sources and interpretation.

### Benefit-cost ratios and net benefits

- Definitions of benefits, costs, net benefits and BCRs.
- Discounting choices, time-period weights and evaluation horizon.
- **Graph:** global sector BCRs across calibrations, with discounting choices and a BCR=1 reference line.
- **Graph:** discounted net benefits alongside the BCR comparison.

??? info "Regional comparisons"

    - **Graph:** regional BCRs and net benefits across sectors and calibrations.
    - Interpretation of zero-cost or undefined ratios.

## References

- Scientific sources for each impact, adaptation curves, calibration and mortality valuation.

## Related pages

- [Doing an ACCREU run](../../run/accreu.md).
