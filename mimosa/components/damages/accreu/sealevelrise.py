from typing import Sequence
from mimosa.common import (
    ConcreteModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalConstraint,
    RegionalEquation,
    value,
    soft_max,
    soft_min,
    Any,
    exp,
    log,
    quant,
    NonNegativeReals,
)

from mimosa.core.model_inputs import ModelInputs

from .utils import (
    AdaptationOptions,
    adaptation_effectiveness_fct,
    dmg_fct_power,
    effective_adaptation_curve,
    optimal_adaptation_costs_fct,
    get_delayed_adaptation_constraint,
)


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs, adaptation_options: AdaptationOptions
):
    """

    The sea-level rise impacts are calculated using the DIVA model. Specifically,
    for this purpose, we compare the Constant Dike Height scenario (“no adaptation / CDH”)
    with three adaptation scenarios: Constant flood protection standards, Doubling
    flood protection standards, and Quadrupling flood protection standards. Importantly,
    we do not use the “optimal adaptation” scenario from DIVA, to avoid double optimisation
    in the IAMs.

    The gross damages are fitted with a power function of global sea-level rise:

    :::mimosa.components.damages.accreu.sealevelrise.gross_dmg_fct_slr
        options:
            show_source: false

    The adaptation function is fitted with a negative-exponential saturation curve, like in
    all three sectors. Subsequently, the residual damages are calculated as:

    $$
    \\href{./#var__slr_damage_costs}{\\text{damages}_{\\text{SLR},t,r}} = \\href{./#var__slr_damage_costs_gross}{\\text{gross damages}_{\\text{SLR},t,r}} \\cdot (1 - \\href{./#var__slr_adaptation_level}{\\text{adapt. level}_{\\text{SLR},t,r}}),
    $$

    <div class="grid cards" markdown>

    -   <h5 class="no-nav">Global damages (without adaptation)</h5>

        ---

        ``` plotly
        {"file_path": "./assets/plots/slr_damages_global.json"}
        ```

    -   <h5 class="no-nav">Global adaptation costs</h5>

        ---

        ``` plotly
        {"file_path": "./assets/plots/slr_adaptation_global.json"}
        ```
    </div>

    ??? regional-fct "Regional damage and adaptation functions"

        === "Damages (without adaptation)"

            ![Regional damage costs (without adaptation)](../../assets/fig/accreu/slr_noadapt_ead.png)

        === "Adaptation costs"

            ![Regional damage costs (without adaptation)](../../assets/fig/accreu/slr_adapt_eff.png)

    <div class="tiny_table table_scrollable extra_small" markdown>

    | Variables created in this module: |
    | --------------------------------- |
    | var::slr_damage_costs_gross |
    | var::slr_adaptation_costs_abs |
    | var::slr_adaptation_costs |
    | var::slr_adaptation_level |
    | var::slr_damage_costs |

    </div>
    """

    constraints = []
    adaptation_type = adaptation_options.adaptation_type
    adaptation_calibration = adaptation_options.calibrations["slr"]

    ## Gross damages:

    m.slr_damages_gross_constant = Param(
        m.regions, initialize=inputs.regional("ACCREU", "slr_noadapt_ead_constant")
    )
    m.slr_damages_gross_prod = Param(
        m.regions, initialize=inputs.regional("ACCREU", "slr_noadapt_ead_prod")
    )
    m.slr_damages_gross_power = Param(
        m.regions, initialize=inputs.regional("ACCREU", "slr_noadapt_ead_power")
    )

    damage_cost_gross_var_name = (
        "slr_damage_costs"
        if adaptation_type == "noadaptation"
        else "slr_damage_costs_gross"
    )
    setattr(
        m,
        damage_cost_gross_var_name,
        Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Gross damages from sea-level rise, without adaptation",
        ),
    )
    constraints.append(
        RegionalEquation(
            getattr(m, damage_cost_gross_var_name),
            gross_dmg_fct_slr,
        )
    )

    ## Adaptation:
    if adaptation_type != "noadaptation":
        m.slr_adaptation_costs_abs = Var(
            m.t,
            m.regions,
            units=quant.unit("currency_unit"),
            bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
            doc="Absolute adaptation costs for sea-level rise, in currency units. Used to calculate the adaptation level",
        )
        m.slr_adaptation_costs = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Adaptation costs for sea-level rise, as a fraction of GDP.",
        )
        m.slr_adaptation_level = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_gross_damages"),
            bounds=(0, 1),
            doc="Adaptation level for sea-level rise, as a fraction of gross damages. 0 means that no damages are avoided, while 1 means that all damages are avoided.",
        )
        m.slr_damage_costs = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Residual damages from sea-level rise, after adaptation. If `noadaptation` is chosen, this variable represents the gross damages.",
        )

        m.slr_adaptation_max_effectiveness = Param(
            m.regions,
            initialize=inputs.regional("ACCREU", "slr_adapt_eff_max_effectiveness"),
        )
        m.slr_adaptation_cost_param = Param(
            m.regions,
            initialize=inputs.regional("ACCREU", "slr_adapt_eff_cost_param"),
        )
        constraints.append(get_delayed_adaptation_constraint("slr_adaptation_costs"))
        constraints.extend(
            [
                # Adaptation effectiveness function
                RegionalEquation(
                    m.slr_adaptation_level,
                    lambda m, t, r: adaptation_effectiveness_fct(
                        m.slr_adaptation_costs_abs[t, r],
                        *effective_adaptation_curve(
                            m,
                            r,
                            m.slr_adaptation_max_effectiveness[r],
                            m.slr_adaptation_cost_param[r],
                            adaptation_calibration,
                        ),
                    ),
                ),
                # Adaptation costs as a fraction of GDP
                RegionalEquation(
                    m.slr_adaptation_costs,
                    lambda m, t, r: m.slr_adaptation_costs_abs[t, r]
                    / m.GDP_gross[t, r],
                ),
                # Residual damages after adaptation
                RegionalEquation(
                    m.slr_damage_costs,
                    lambda m, t, r: m.slr_damage_costs_gross[t, r]
                    * (1 - m.slr_adaptation_level[t, r]),
                ),
            ]
        )

        if adaptation_options.uses_analytical_adaptation:
            constraints.append(
                # Calculate analytically the optimal level of adaptation
                RegionalEquation(
                    m.slr_adaptation_costs_abs,
                    lambda m, t, r: optimal_adaptation_costs_fct(
                        m,
                        t,
                        m.slr_damage_costs_gross[t, r] * m.GDP_gross[t, r],
                        *effective_adaptation_curve(
                            m,
                            r,
                            m.slr_adaptation_max_effectiveness[r],
                            m.slr_adaptation_cost_param[r],
                            adaptation_calibration,
                        ),
                        scale=0.00001,
                    ),
                )
            )

    return constraints


def gross_dmg_fct_slr(m, t, r):
    """
    $$
        \\href{./#var__slr_damage_costs_gross}{\\text{gross damages}_{\\text{SLR},t,r}}
        = (a_r + b_r \\cdot \\href{./#var__total_SLR}{\\text{SLR}_t} {}^ {c_r})
        - (a_r + b_r \\cdot \\href{./#var__total_SLR}{\\text{SLR}_0} {}^ {c_r})
    $$
    """
    return (
        dmg_fct_power(
            m,
            t,
            m.slr_damages_gross_constant[r],
            m.slr_damages_gross_prod[r],
            m.slr_damages_gross_power[r],
            x="total_SLR",
        )
        * m.damage_scale_factor
    )
