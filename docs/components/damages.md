---
icon: material/home-flood
---

[:octicons-arrow-left-24: Back to general structure](index.md)

Climate impacts in MIMOSA are calculated using the [COACCH](https://www.coacch.eu/) damage functions, developed in 2023
(see [van der Wijst et al., 2023](https://doi.org/10.1038/s41558-023-01636-1)).

:::mimosa.components.damages.coacch.get_constraints


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

| Climate change impact area | Model source | Variable used in CGE |
| -- | -- | -- |
| :fontawesome-solid-wheat-awn: Agriculture | [EPIC biophysical model](https://doi.org/10.1016%2Fj.agsy.2013.05.008)  and [GLOBIOM model](https://doi.org/10.1016%2Fj.enpol.2010.03.030) | (Change in) Crop yield |
| :material-forest: Forestry | [G4M model](https://doi.org/10.1073%2Fpnas.0710616105)  | (Change in) Net physical wood production per hectare |
| :material-fish: Fishery | [DBEM envelope model](https://doi.org/10.1016%2Fj.ecolmodel.2015.12.018)  and [DSFM food web model](https://doi.org/10.1098%2Frstb.2012.0231) | (Change in) Fish catches |
| :material-waves-arrow-up: Sea-level rise | [DIVA model](https://doi.org/10.1073%2Fpnas.1222469111) | - Annual land loss due to submergence<br>- Expected annual damages to assets<br>- Expected annual number of people flooded<br>- Annual protection costs |
| :material-home-flood: Riverine floods | [GLOFRIS model](https://doi.org/10.1088%2F1748-9326%2F8%2F4%2F044019) | - Expected annual damages for the industrial, commercial, and residential sectors<br>- Expected annual number of people flooded | 
| :fontawesome-solid-road: Road transportation | [OSDaMage model](https://doi.org/10.5194%2Fnhess-21-1011-2021) | Expected annual damages for the road infrastructure |
| :material-wind-turbine: Energy supply | [Schleypen et al. (2019)](https://www.coacch.eu/wp-content/uploads/2020/05/D2.4_after-revision-to-upload.pdf) | Changes in wind and hydropower production |
| :material-air-conditioner: Energy demand | [Schleypen et al. (2019)](https://www.coacch.eu/wp-content/uploads/2020/05/D2.4_after-revision-to-upload.pdf) | Changes in energy demand by households and by the industrial, agricultural and service sectors for coal, oil, gas, and electricity |
| :material-human-male-male: Labour productivity | [Dasgupta et al. (2022)](https://doi.org/10.1016%2FS2542-5196%2821%2900170-4) | Changes in per capita production of value added |