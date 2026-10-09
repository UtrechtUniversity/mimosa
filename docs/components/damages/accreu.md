---
icon: material/gamepad-circle
---

[:octicons-arrow-left-24: Back to damage models](index.md)

## Overview

- Purpose and scope of the ACCREU damage and adaptation model.
- Impacts included and links to the underlying models and studies.

## Labour productivity

### Damages

- Damage equation and temperature driver.
- Regional coefficients, units and sources.
- Initial-period subtraction and treatment of benefits.

### Adaptation

- Adaptation effectiveness equation and expenditure.
- Regional adaptation coefficients and calibration.
- Avoided and residual damages.
- Relationship to combined adaptation.

### Curves and results

- **Graph:** regional labour-productivity damages versus temperature.
- **Graph:** labour-productivity adaptation effectiveness versus expenditure, comparing calibrations.
- **Graph:** gross, avoided and residual labour damages with adaptation expenditure on a matched climate pathway.

## Riverine flooding

### Damages

- Damage equation and temperature driver.
- Regional coefficients, units and sources.
- Initial-period subtraction.

### Adaptation

- Adaptation effectiveness equation and expenditure.
- Regional adaptation coefficients and calibration.
- Avoided and residual damages.
- Relationship to combined adaptation.

### Curves and results

- **Graph:** regional riverine-flood damages versus temperature.
- **Graph:** riverine adaptation effectiveness versus expenditure, comparing calibrations.
- **Graph:** gross, avoided and residual riverine damages with adaptation expenditure on a matched climate pathway.

## Sea-level rise

### Damages

- Damage equation and sea-level-rise driver.
- Regional coefficients, units and sources.
- Initial-period subtraction.

### Adaptation

- Adaptation effectiveness equation and expenditure.
- Regional adaptation coefficients and calibration.
- Avoided and residual damages.
- Treatment of SLR adaptation in separate and combined configurations.

### Curves and results

- **Graph:** regional SLR damages versus sea level.
- **Graph:** SLR adaptation effectiveness versus expenditure, comparing calibrations.
- **Graph:** gross, avoided and residual SLR damages with adaptation expenditure on a matched climate pathway.

## Mortality

### Heat- and cold-related impacts

=== "Heat-related mortality"

    - Mortality equation, temperature driver and population dependence.
    - Regional coefficients and mortality units.
    - Initial-period subtraction and sources.

=== "Cold-related mortality"

    - Mortality equation and temperature driver.
    - Regional coefficients and mortality units.
    - Initial-period subtraction, benefits and sources.

### Valuation and adaptation coverage

- Mortality monetisation option and valuation assumptions.
- Treatment of heat-related losses and cold-related benefits.
- Scope of adaptation in the current model and relationship to mitigation.
- Output variables and units.

### Curves and results

- **Graph:** heat- and cold-related mortality versus temperature, in separate panels with appropriate units.
- **Graph:** mortality valuation across selected scenarios and regions.

## Combined labour and riverine adaptation

- Combined adaptation coverage and relationship to separate sector curves.
- Combined effectiveness equation, expenditure and regional coefficients.
- Calibration assumptions and sector weights.
- Aggregation without double-counting impacts.
- **Graph:** combined versus separate adaptation curves and residual damages.

## From sector impacts to economic outcomes

- Aggregation of gross, avoided and residual damages across sectors and regions.
- Adaptation expenditure and its relationship to damage costs.
- Market damages versus monetised mortality.
- Effects on GDP, consumption and welfare.
- **Diagram:** climate drivers, impact-specific damages and adaptation through to expenditure, mortality valuation and economic outcomes.

## Shared adaptation settings

=== "No adaptation"

    - Meaning of `noadaptation`.
    - Damage and expenditure outputs.

=== "Separate adaptation"

    - Sector-specific adaptation choices and expenditure.
    - Sectors protected by each adaptation curve.
    - Aggregation of costs and residual damages.

=== "Combined adaptation"

    - Combined adaptation coverage and relationship to separate adaptation.
    - Treatment of SLR and mortality.
    - Aggregation without double-counting sectors.

## Choosing adaptation expenditure

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

## Optimisation strategy

=== "Joint CBA"

    - Mitigation and adaptation choices in the joint workflow.
    - Solver-controlled and analytical adaptation variants.

=== "Mitigation then adaptation"

    - Order of the mitigation optimisation and adaptation calculation.
    - Required settings and restrictions.
    - Reasons for differences from the joint workflow.

## Configuration options

- Table of options, configuration paths, allowed values and effects.
- Links to the [parameter reference](../../parameters.md) for defaults and types.
- Effectiveness scaling and delayed adaptation.
- Related mortality monetisation and valuation settings.

## Calibration

=== "Original calibration"

    - Source-model coefficients and interpretation of `accreu`.
    - Coefficient provenance and regional variation.

=== "Literature calibrations"

    - Low, central and high calibration choices.
    - Changes to effectiveness and expenditure coefficients.
    - Distinction between calibration targets and uncertainty.
    - Evidence sources and interpretation.

### Combined calibration

- Sector weights, effectiveness cap and supporting evidence.
- Table of calibration factors and benchmarks.

??? info "Existing calibration notes"

    The ACCREU adaptation curves can use either the original source-model calibration
    or low, central, and high literature-based realised-effectiveness calibrations.
    This applies to both separate and combined adaptation:

    ```yaml
    model structure:
      damage module: ACCREU
    economics:
      damages:
        accreu:
          adaptation: combined
          adaptation_calibration: literature
          adaptation_determination: analytical_optimum
          cba_strategy: mitigation_then_adaptation
    ```

    The default value is `accreu`, which preserves the original coefficients. The
    three literature settings retain the original regional rankings but apply the
    following sectoral factors:

    | Calibration       | Sector                       | Maximum-effectiveness factor | Adaptation cost multiplier | Approximate global BCR at 5% |
    | ----------------- | ---------------------------- | ---------------------------: | -------------------------: | ---------------------------: |
    | `literature_low`  | Labour productivity          |                        0.741 |                        6.00 |                          2.0 |
    |                   | Riverine flooding            |                        0.412 |                        6.00 |                          2.1 |
    |                   | Sea-level rise               |                        0.439 |                        8.00 |                          4.7 |
    |                   | Combined labour and riverine |                        0.645 |                        6.00 |                          2.5 |
    | `literature`      | Labour productivity          |                        1.000 |                        1.00 |                          2.4 |
    |                   | Riverine flooding            |                        0.618 |                        1.00 |                          4.6 |
    |                   | Sea-level rise               |                        0.659 |                        4.00 |                          7.8 |
    |                   | Combined labour and riverine |                        0.889 |                        1.00 |                          4.3 |
    | `literature_high` | Labour productivity          |                        1.977 |                        0.50 |                          3.7 |
    |                   | Riverine flooding            |                        0.721 |                        0.50 |                          6.9 |
    |                   | Sea-level rise               |                        0.933 |                        2.00 |                         14.0 |
    |                   | Combined labour and riverine |                        1.250 |                        0.25 |                          8.8 |

    The cost parameter is the coefficient `b` in
    `E(C) = Emax * (1 - exp(-b * C))`. MIMOSA divides `b` by the adaptation cost
    multiplier. A multiplier of 2 therefore means that twice as much expenditure is
    needed to reach the same relative point on the adjusted adaptation curve, while
    0.5 means half as much. Because maximum effectiveness also changes, this is not
    necessarily the cost of reaching the same absolute avoided-damage percentage.
    `literature_low` represents the conservative end of the evidence range (lower
    realised effectiveness and higher cost), while
    `literature_high` represents the optimistic end (higher realised effectiveness
    and lower cost). The previously available separate-sector central calibration is
    unchanged. These are
    calibration targets rather than statistical estimates of the coefficients. The
    benchmarks are
    based on [IPCC AR6 WGII Chapter 9](https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-9/),
    the [World Bank flood-resilience review](https://documents1.worldbank.org/curated/en/099122325103032001/pdf/P178843-a69ab123-c5a7-4a7e-8686-82b20fe83ac7.pdf),
    and [IPCC AR6 WGII Cross-Chapter Paper 2](https://www.ipcc.ch/report/ar6/wg2/downloads/report/IPCC_AR6_WGII_FD_CCP2.pdf).
    The reported BCRs cover 2020--2100 and weight discounted annual flows by the
    model's actual period lengths: five years through 2050 and ten years thereafter.

    ### Combined adaptation calibration

    The combined curve protects gross labour-productivity and riverine-flood damages.
    It does not protect mortality, so it is not literally a calibration of every
    non-SLR impact in ACCREU. Under the default MIMOSA scenario, labour productivity
    accounts for 70.9% and riverine flooding for 29.1% of their combined discounted
    gross damages through 2100. These shares give the low and central combined
    maximum-effectiveness factors:

    `0.709 * 0.741 + 0.291 * 0.412 = 0.645`

    `0.709 * 1.000 + 0.291 * 0.618 = 0.889`

    The same weighted calculation gives 1.612 for the high calibration, but this
    would raise the maximum avoided-damage share above one in some regions. The high
    factor is therefore capped at 1.250, which keeps the largest regional maximum at
    approximately 0.93. Its adaptation cost multiplier is set to 0.25 to place its
    BCR near the upper part of the literature range while respecting this physical
    cap.

    | Combined calibration | Global BCR at 5% | Discounted realised effectiveness |
    | -------------------- | ---------------: | --------------------------------: |
    | `literature_low`     |             2.45 |                               10% |
    | `literature`         |             4.29 |                               29% |
    | `literature_high`    |             8.84 |                               51% |

    The combined BCR envelope is anchored in several independent assessments. IPCC
    AR6 WGII reports BCRs of 1--11.5 at a 5% discount rate for 19 Green Climate Fund
    adaptation projects, with a median of 2.4 and an aggregate ratio of 3.5. The
    [Global Commission on Adaptation](https://gca.org/4-things-to-know-about-the-global-adaptation-challenge/)
    reports a cross-sector range of 2--10, while the World Bank's
    [_Lifelines_ report](https://documents1.worldbank.org/curated/en/111181560974989791/pdf/Lifelines-The-Resilient-Infrastructure-Opportunity.pdf)
    reports approximately four dollars of benefit per dollar invested in resilient
    infrastructure. See [IPCC AR6 WGII Chapter 9](https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-9/).
    The [UNEP Adaptation Gap Report 2025](https://www.unep.org/resources/adaptation-gap-report-2025)
    provides global cost estimates but no corresponding avoided-damage percentage;
    the combined maximum-effectiveness factors should therefore be interpreted as a
    transparent translation of the BCR evidence, not as directly estimated physical
    coefficients.

## Benefit-cost ratios and net benefits

- Definitions of benefits, costs, net benefits and BCRs.
- Discounting choices, time-period weights and evaluation horizon.
- **Graph:** global sector BCRs across calibrations, with discounting choices and a BCR=1 reference line.
- **Graph:** discounted net benefits alongside the BCR comparison.

??? info "Regional comparisons"

    - **Graph:** regional BCRs and net benefits across sectors and calibrations.
    - Interpretation of zero-cost or undefined ratios.

## ACCREU_CGE {id="accreu-cge"}

- Aggregate fitted damage curves and their sources.
- Differences from the explicit ACCREU impact and adaptation model.
- Available options, regional coefficients and outputs.

??? info "Regional coefficients and data sources"

    - Table of damage and adaptation coefficients, units, regional coverage and sources.
    - Downloadable regional coefficient table.
    - Links to the input files and relevant parameter-reference entries.

??? info "Assumptions and limitations"

    - Coverage of climate impacts and adaptation.
    - Fitting ranges and extrapolation.
    - Reference conditions, negative benefits and aggregation conventions.

## References

- Scientific sources for each impact, adaptation curves, calibration and mortality valuation.

## Related pages

- [Doing an ACCREU run](../../run/accreu.md).
