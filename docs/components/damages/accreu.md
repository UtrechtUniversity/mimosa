---
icon: material/gamepad-circle
---

[:octicons-arrow-left-24: Back to damage models](index.md)

:::mimosa.components.damages.accreu.all_damages.get_constraints

## Impact sectors

### :material-home-flood: Riverine flooding

:::mimosa.components.damages.accreu.riverine_flooding.get_constraints

### :material-human-male-male: Labour productivity

:::mimosa.components.damages.accreu.labour_productivity.get_constraints

### :material-waves-arrow-up: Sea level rise

:::mimosa.components.damages.accreu.sealevelrise.get_constraints

### :material-heart-pulse: Mortality

:::mimosa.components.damages.accreu.mortality.get_constraints

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

??? info "Numerical implementation"

    - Smoothing and boundary behaviour.
    - Expenditure bounds and delayed-adaptation implementation.

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
