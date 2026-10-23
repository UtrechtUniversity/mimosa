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

## Related pages

- [Doing an ACCREU run](../../run/accreu.md).
