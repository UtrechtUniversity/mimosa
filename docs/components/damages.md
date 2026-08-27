---
icon: material/home-flood
---

[:octicons-arrow-left-24: Back to general structure](index.md)

Climate impacts in MIMOSA are calculated using the [COACCH](https://www.coacch.eu/) damage functions, developed in 2023
(see [van der Wijst et al., 2023](https://doi.org/10.1038/s41558-023-01636-1)).

:::mimosa.components.damages.coacch.get_constraints

## ACCREU adaptation calibration

The ACCREU adaptation curves can use either the original source-model calibration
or low, central, and high literature-based realised-effectiveness calibrations.
This applies to both separate and combined adaptation:

```yaml
model structure:
  damage module: ACCREU
  damage module options:
    ACCREU_adaptation: combined
    ACCREU_adaptation_calibration: literature
    ACCREU_adaptation_determination: analytical_optimum
    ACCREU_CBA_strategy: mitigation_then_adaptation
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

## Damage functions and coefficients

??? info "Visualisation of damage functions and damage coefficients"

    [:material-download: Download COACCH damage function coefficients](../assets/data/COACCH_damage_function_coefficients_IMAGE_regions.xlsx){.md-button}

    === "Non-SLR damages"

        <div style="overflow: scroll;" markdown>
        ``` plotly
        {"file_path": "./assets/plots/coacch_all_curves_noslr.json"}
        ```
        </div>

    === "SLR damages (optimal adaptation)"

        <div style="overflow: scroll;" markdown>
        ``` plotly
        {"file_path": "./assets/plots/coacch_all_curves_slr_ad.json"}
        ```
        </div>

    === "SLR damages (no adaptation)"

        <div style="overflow: scroll;" markdown>
        ``` plotly
        {"file_path": "./assets/plots/coacch_all_curves_slr_noad.json"}
        ```
        </div>

    === "Combined SLR and non-SLR damages"

        <div style="overflow: scroll;" markdown>
        ``` plotly
        {"file_path": "./assets/plots/coacch_all_curves_combined.json"}
        ```
        </div>

## Impact sectors used in the damage functions

| Climate change impact area                     | Model source                                                                                                                                 | Variable used in CGE                                                                                                                                    |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| :fontawesome-solid-wheat-awn: Agriculture      | [EPIC biophysical model](https://doi.org/10.1016%2Fj.agsy.2013.05.008) and [GLOBIOM model](https://doi.org/10.1016%2Fj.enpol.2010.03.030)    | (Change in) Crop yield                                                                                                                                  |
| :material-forest: Forestry                     | [G4M model](https://doi.org/10.1073%2Fpnas.0710616105)                                                                                       | (Change in) Net physical wood production per hectare                                                                                                    |
| :material-fish: Fishery                        | [DBEM envelope model](https://doi.org/10.1016%2Fj.ecolmodel.2015.12.018) and [DSFM food web model](https://doi.org/10.1098%2Frstb.2012.0231) | (Change in) Fish catches                                                                                                                                |
| :material-waves-arrow-up: Sea-level rise       | [DIVA model](https://doi.org/10.1073%2Fpnas.1222469111)                                                                                      | - Annual land loss due to submergence<br>- Expected annual damages to assets<br>- Expected annual number of people flooded<br>- Annual protection costs |
| :material-home-flood: Riverine floods          | [GLOFRIS model](https://doi.org/10.1088%2F1748-9326%2F8%2F4%2F044019)                                                                        | - Expected annual damages for the industrial, commercial, and residential sectors<br>- Expected annual number of people flooded                         |
| :fontawesome-solid-road: Road transportation   | [OSDaMage model](https://doi.org/10.5194%2Fnhess-21-1011-2021)                                                                               | Expected annual damages for the road infrastructure                                                                                                     |
| :material-wind-turbine: Energy supply          | [Schleypen et al. (2019)](https://www.coacch.eu/wp-content/uploads/2020/05/D2.4_after-revision-to-upload.pdf)                                | Changes in wind and hydropower production                                                                                                               |
| :material-air-conditioner: Energy demand       | [Schleypen et al. (2019)](https://www.coacch.eu/wp-content/uploads/2020/05/D2.4_after-revision-to-upload.pdf)                                | Changes in energy demand by households and by the industrial, agricultural and service sectors for coal, oil, gas, and electricity                      |
| :material-human-male-male: Labour productivity | [Dasgupta et al. (2022)](https://doi.org/10.1016%2FS2542-5196%2821%2900170-4)                                                                | Changes in per capita production of value added                                                                                                         |
