# Doing an ACCREU run

## Mitigation vs adaptation effort

To use the ACCREU damage and adaptation curves, select the [ACCREU damage module](#param__model%20structure.damage%20module):

```python hl_lines="2"
params = load_params()
params["model structure"]["damage module"] = "ACCREU"
model = MIMOSA(params)
```

This allows for the comparison of mitigation and adaptation efforts. The following table summarises the main different scenarios that can be run, and whether they include mitigation and/or adaptation.

| Scenario | Mitigation | Adaptation |
|---|---|---|
| [**No policy**](#no-policy) | No | No |
| [**Mitigation only CBA**](#mitigation-only-cba) | Yes | No |
| [**Adaptation only**](#adaptation-only) | No | Yes |
| [**Mitig. and adapt. CBA (sequential)**](#mitig-and-adapt-cba-sequential) | Yes | Yes (optimised after mitigation) |
| [**Mitig. and adapt. CBA (joint)**](#mitig-and-adapt-cba-joint) | Yes | Yes (optimised at same time as mitigation) |

## Running the different scenarios

=== "No policy"

    ```python
    --8<-- "tests/runs/run_accreu_nopolicy.py"
    ```

    In the **no policy** scenario, no adaptation or mitigation is undertaken. We adopt the SSP-2 assumptions regarding economic growth and emissions, and do not implement any climate policy beyond what is currently in place. This scenario is set against all other scenarios in which some form of additional policy is implemented.

=== "Mitigation only CBA"

    ```python
    --8<-- "tests/runs/run_accreu_mit.py"
    ```

    In the **mitigation only CBA** scenario, a cost-benefit analysis is carried out in which mitigation is the only form of climate policy. There is no adaptation.

=== "Adaptation only"

    ```python
    --8<-- "tests/runs/run_accreu_ada.py"
    ```

    In the **adaptation only** scenario, the only policy response to climate change is through adaptation. The model optimises the regional adaptation costs for each sector, and uses these to reduce the damages in each sector according to the adaptation level. No mitigation is undertaken.

=== "Mitig. and adapt. CBA (sequential)"

    ```python
    --8<-- "tests/runs/run_accreu_mit_then_ada.py"
    ```

    In the **sequential mitig. and adaptation CBA scenario**, a two-step approach is taken. First, a cost-benefit analysis is carried out in which only mitigation measures are considered (this is identical to the [mitigation-only scenario](#mitigation-only-cba)). This emissions pathway is then used to calculate the optimal level of additional adaptation. This scenario explicitly avoids the weighing of adaptation against mitigation.

=== "Mitig. and adapt. CBA (joint)"

    ```python
    --8<-- "tests/runs/run_accreu_mit_ada_joint.py"
    ```

    In the **joint mitig. and adaptation CBA scenario**, a cost-benefit analysis is carried out in which adaptation and mitigation policies are implemented simultaneously. As such, the model weighs  expenditures on adaptation and mitigation against one another. This relies heavily on the assumptions that all regions will adapt optimally to climate change in all time periods. If adaptation turns out to be less effective than assumed, this scenario will show insufficient mitigation, and vice versa. This scenario is therefore not recommended as the main approach for policy analysis, but is useful for understanding the interactions between adaptation and mitigation.

## Changing assumptions

#### Mortality monetisation

By default, the ACCREU damage module monetises mortality using the Value of Statistical Life (VSL) approach. Monetisation can be switched off using the [`monetise mortality`](#param__economics.damages.accreu.monetise_mortality) parameter:

```python hl_lines="3"
params = load_params()
params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["monetise_mortality"] = False
model = MIMOSA(params)
```

#### ACCREU vs literature-based adaptation calibration

The ACCREU adaptation effectiveness curves have been calibrated using a single model per impact sector (GLOFRIS for riverine flooding, DIVA for sea-level rise, and an empirical study for labour productivity). However, it is also possible to run MIMOSA using adaptation curves that have been calibrated to the broader literature, by setting the [`adaptation calibration`](#param__economics.damages.accreu.adaptation_calibration) parameter to `literature` (for medium estimates of the literature range), `literature_low` (for low estimates) or `literature_high` (for high end of the literature range):

```python hl_lines="3"
params = load_params()
params["model structure"]["damage module"] = "ACCREU"
params["economics"]["damages"]["accreu"]["adaptation_calibration"] = "literature"
model = MIMOSA(params)
```

More details on these adaptation effectiveness functions are available in the [ACCREU documentation page](../components/damages/accreu.md#riverine-flooding).


#### Delayed adaptation and mitigation

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
