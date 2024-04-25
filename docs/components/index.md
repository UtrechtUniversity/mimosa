# Documentation of model components

The MIMOSA model consists of several sub-modules, called model components. Each component is made up of multiple variables (global or regional), parameters and equations (called constraints).

<div class="grid cards" markdown>

-   #### :fontawesome-regular-money-bill-1: Economics

    ---

    Cobb-Douglas production function, investments, consumption and capital stock

    [:octicons-arrow-right-24: Read more](economics.md){.md-button}


-   #### :material-arrow-projectile-multiple: Welfare

    ---

    Welfare and the utility function

    [:octicons-arrow-right-24: Read more](welfare.md){.md-button}

-   #### :octicons-cloud-16: Emissions and temperature

    ---

    - Baseline emissions, regional mitigated emissions and cumulative emissions
    - Temperature module
    - Constraints on emissions like inertia

    [:octicons-arrow-right-24: Read more](emissions.md){.md-button}

-   #### :material-wind-turbine: Mitigation

    ---

    Mitigation costs, Marginal Abatement Cost curve and technological learning

    [:octicons-arrow-right-24: Read more](mitigation.md){.md-button}
  
-   #### :material-waves-arrow-up: Sea-level rise

    ---

    Determines the level of global sea-level rise

    [:octicons-arrow-right-24: Read more](sealevelrise.md){.md-button}

-   #### :material-home-flood: Damages

    ---

    Temperature related damages and sea-level rise related damages

    [:octicons-arrow-right-24: Read more](damages.md){.md-button}


-   #### :fontawesome-solid-people-carry-box: Effort-sharing

    ---

    `Optional` Various effort-sharing regimes to distribute the mitigation (and sometimes damage) costs

    [:octicons-arrow-right-24: Read more](effortsharing.md){.md-button}


-   #### :material-earth: Emission trading

    ---

    `Optional` Allows for global trade of emission reductions

    [:octicons-arrow-right-24: Read more](emissiontrading.md){.md-button}

-   #### :fontawesome-solid-money-bill-transfer: Financial transfers

    ---

    `Optional` Financial transfer schemes like a global damage cost pool

    [:octicons-arrow-right-24: Read more](financialtransfers.md){.md-button}



</div>

----

:::mimosa.abstract_model.create_abstract_model