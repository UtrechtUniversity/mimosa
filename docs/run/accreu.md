# Doing an ACCREU run

## Getting started

- Select the ACCREU damage module and choose adaptation settings.
- Minimal imports and configuration example.
- Link to [ACCREU damages and adaptation by impact](../components/damages/accreu.md).

## Running different scenarios

=== "No policy"

    ```python
    --8<-- "tests/runs/run_accreu_nopolicy.py"
    ```

=== "Mitigation only CBA"

    ```python
    --8<-- "tests/runs/run_accreu_mit.py"
    ```

=== "Adaptation only"

    ```python
    --8<-- "tests/runs/run_accreu_ada.py"
    ```

=== "Mitigation and adaptation CBA (sequential)"

    ```python
    --8<-- "tests/runs/run_accreu_mit_then_ada.py"
    ```

=== "Mitigation and adaptation CBA (joint)"

    ```python
    --8<-- "tests/runs/run_accreu_mit_ada_joint.py"
    ```

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

=== "Reduced adaptation effectiveness"

    ```python
    --8<-- "tests/runs/run_accreu_ada_red_eff.py"
    ```

=== "Implementation gap"

    ```python
    --8<-- "tests/runs/run_accreu_ada_impl_gap.py"
    ```

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
