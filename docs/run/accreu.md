# Doing an ACCREU run

## Getting started

- Select the ACCREU damage module and choose adaptation settings.
- Minimal imports and configuration example.
- Link to [ACCREU damages and adaptation by impact](../components/damages/accreu.md).

## Running different scenarios

=== "No policy"

    - Configuration and minimal example.
    - Use of `run_nopolicy_baseline()`.
    - Results to inspect and save.

=== "Mitigation only"

    - Configuration and minimal example.
    - Optimisation without adaptation.
    - Results to inspect and save.

=== "Adaptation only"

    - Configuration and minimal example.
    - Analytical adaptation with no mitigation.
    - Difference between `run_simulation()` and `run_nopolicy_baseline()`.
    - Results to inspect and save.

=== "Joint CBA"

    - Configuration and minimal example.
    - Joint mitigation and adaptation workflow.
    - Results to inspect and save.

=== "Sequential CBA"

    - Configuration and minimal example.
    - Mitigation-then-adaptation workflow and required settings.
    - Results to inspect and save.

## Changing assumptions

- Separate versus combined adaptation.
- Original versus literature-based calibration.
- Mortality monetisation and valuation.
- Delayed adaptation and reduced realised effectiveness.

## Reading and comparing results

- Important output variables, units and saved files.
- Distinction between market damage, mortality valuation and adaptation expenditure.
- Common assumptions for comparable scenarios.
- **Graph:** temperature and emissions across the five scenarios.
- **Graph:** market damages, monetised mortality and adaptation expenditure across scenarios.
- **Graph:** consumption or welfare effects across scenarios.

## Sensitivity experiments

- Mortality on/off, delayed adaptation and reduced effectiveness.
- Separate versus combined adaptation.
- **Graph:** selected sensitivity comparisons with clearly labelled assumptions.

??? info "Advanced: replaying controls"

    - Example retaining chosen controls while changing realised effectiveness.
    - Difference between reduced effectiveness and reduced expenditure.
    - Interpretation of the resulting pathway.

??? info "Advanced: SCC comparison"

    - Optional sector SCC example using `diagnostics/scc.py`.
    - Pulse, discounting, currency and control assumptions.
    - **Graph:** SCC sector breakdown for selected adaptation assumptions.

??? info "Scripts and figure regeneration"

    - Scenario results and timings: planned `diagnostics/accreu_scenarios.py`.
    - BCR calculations and tables: `diagnostics/adaptation_bcr.py`.
    - Damage and adaptation curves: planned `fig_accreu_curves.py`.
    - Saved-result figures: planned `fig_accreu_results.py`.
    - Short executable examples under `tests/runs/`.
    - Plot generation commands, saved tables and figure files.

## Related pages

- [Simulation and optimisation](simulation.md).
- [Doing a baseline run](baseline.md).
- [ACCREU damages and adaptation](../components/damages/accreu.md).
