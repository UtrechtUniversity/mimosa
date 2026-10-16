# Doing an ACCREU run

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

=== "Mitig. and adapt. CBA (sequential)"

    ```python
    --8<-- "tests/runs/run_accreu_mit_then_ada.py"
    ```

=== "Mitig. and adapt. CBA (joint)"

    ```python
    --8<-- "tests/runs/run_accreu_mit_ada_joint.py"
    ```

## Changing assumptions

- Original versus literature-based calibration.
- Mortality monetisation and valuation.
- Delayed adaptation and mitigation.

## Sensitivity experiments

=== "Reduced adaptation effectiveness"

    ```python
    --8<-- "tests/runs/run_accreu_ada_red_eff.py"
    ```

=== "Implementation gap"

    ```python
    --8<-- "tests/runs/run_accreu_ada_impl_gap.py"
    ```

??? info "BCR of adaptation"

    - BCR calculations and tables: `diagnostics/adaptation_bcr.py`.

## Related pages

- [Simulation and optimisation](simulation.md).
- [Doing a baseline run](baseline.md).
- [ACCREU damages and adaptation](../components/damages/accreu.md).
