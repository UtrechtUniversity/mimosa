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
    dmg_fct_linear,
    effective_adaptation_curve,
    optimal_adaptation_costs_fct,
    get_delayed_adaptation_constraint,
)


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs, adaptation_options: AdaptationOptions
):
    """

    The impact of climate change on labour productivity can be decomposed in two types:
    heat-related expected annual costs due to warming (e.g. hot regions get hotter, leading
    to reduced labour productivity), and cold-related expected annual benefits due to less cold days
    (especially relevant for currently cold regions).

    :::mimosa.components.damages.accreu.labour_productivity.gross_dmg_fct_labourprod
        options:
            show_source: false

    :::mimosa.components.damages.accreu.labour_productivity.benefits_dmg_fct_labourprod
        options:
            show_source: false

    The adaptation curve, which only applies to heat-related gross damages, is fitted
    with a negative-exponential saturation curve, like in all three sectors. This leads to
    the residual, heat related damages:

    $$
    \\href{./#var__labourprod_damage_costs}{\\text{damages}_{\\text{labourprod},t,r}}
    = \\href{./#var__labourprod_damage_costs_gross}{\\text{gross damages}_{\\text{labourprod},t,r}} \\cdot (1 - \\href{./#var__labourprod_adaptation_level}{\\text{adapt. level}_{\\text{labourprod},t,r}}).
    $$

    The final, net damages are calculated as the sum of the heat-related residual damages and the cold-related benefits:

    $$
    \\href{./#var__labourprod_damage_costs_net}{\\text{net damages}_{\\text{labourprod},t,r}}
    = \\href{./#var__labourprod_damage_costs}{\\text{damages}_{\\text{labourprod},t,r}}
    + \\href{./#var__labourprod_damage_costs_benefits}{\\text{benefits}_{\\text{labourprod},t,r}}
    $$

    <div class="grid cards" markdown>

    -   <h5 class="no-nav">Global damages (heat- and cold-related, without adapt.)</h5>

        ---

        ``` plotly
        {"file_path": "./assets/plots/labourprod_damages_global.json"}
        ```

    -   <h5 class="no-nav">Global adaptation costs (only for heat-related damages)</h5>

        ---

        ``` plotly
        {"file_path": "./assets/plots/labourprod_adaptation_global.json"}
        ```
    </div>

    ??? regional-fct "Regional damage and adaptation functions"

        === "Damages (without adaptation, heat-related)"

            ![Regional damage costs (without adaptation)](../../assets/fig/accreu/labourprod_noadapt_ead.png)

        === "Benefits (from reduced cold)"

            ![Regional benefits from reduced cold](../../assets/fig/accreu/labourprod_benefit_cdd.png)

        === "Adaptation costs"

            ![Regional damage costs (without adaptation)](../../assets/fig/accreu/labourprod_adapt_eff.png)


    <div class="tiny_table table_scrollable extra_small" markdown>

    | Variables created in this module: |
    | --------------------------------- |
    | var::labourprod_damage_costs_gross |
    | var::labourprod_damage_costs_benefits |
    | var::labourprod_adaptation_costs_abs |
    | var::labourprod_adaptation_costs |
    | var::labourprod_adaptation_level |
    | var::labourprod_damage_costs |
    | var::labourprod_damage_costs_net |

    </div>

    """

    constraints = []

    adaptation_type = adaptation_options.adaptation_type
    adaptation_calibration = adaptation_options.calibrations["labourprod"]

    ## Gross damages:

    damage_cost_gross_var_name = (
        "labourprod_damage_costs"
        if adaptation_type == "noadaptation"
        else "labourprod_damage_costs_gross"
    )

    setattr(
        m,
        damage_cost_gross_var_name,
        Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Gross damages from heat-related labour productivity loss (e.g. hot regions get hotter), without adaptation",
        ),
    )

    m.labourprod_damages_gross_constant = Param(
        m.regions,
        initialize=inputs.regional("ACCREU", "labourprod_noadapt_ead_constant"),
    )
    m.labourprod_damages_gross_linear = Param(
        m.regions, initialize=inputs.regional("ACCREU", "labourprod_noadapt_ead_linear")
    )

    constraints.append(
        RegionalEquation(
            getattr(m, damage_cost_gross_var_name), gross_dmg_fct_labourprod
        )
    )

    ## Benefits from less cooling demand due to higher temperatures (negative damages):

    m.labourprod_damage_costs_benefits = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_GDP"),
        doc="Benefits from reduced cold days for labour productivity (e.g. cold regions get less cold). No adaptation is applied to these benefits, as they are not related to heat stress.",
    )

    m.labourprod_damages_benefits_constant = Param(
        m.regions,
        initialize=inputs.regional("ACCREU", "labourprod_benefit_cdd_constant"),
    )
    m.labourprod_damages_benefits_linear = Param(
        m.regions, initialize=inputs.regional("ACCREU", "labourprod_benefit_cdd_linear")
    )

    constraints.append(
        RegionalEquation(
            m.labourprod_damage_costs_benefits, benefits_dmg_fct_labourprod
        )
    )

    ## Adaptation (only for costs, doesn't apply to benefits):

    if adaptation_type == "sectoral":
        m.labourprod_adaptation_costs_abs = Var(
            m.t,
            m.regions,
            units=quant.unit("currency_unit"),
            doc="Adaptation costs for labour productivity (absolute values) (applied only to heat-related damages, not cold-related benefits)",
            bounds=lambda m, t, r: (0, 0.1 * m.baseline_GDP[t, r]),
        )
        m.labourprod_adaptation_costs = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Adaptation costs for labour productivity (as a fraction of GDP) (applied only to heat-related damages, not cold-related benefits)",
        )
        m.labourprod_adaptation_level = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_gross_damages"),
            bounds=(0, 1),
            doc="Adaptation level for labour productivity (applied only to heat-related damages, not cold-related benefits)",
        )
        m.labourprod_damage_costs = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Residual damages for labour productivity after adaptation (heat-related component only)",
        )

        m.labourprod_adaptation_max_effectiveness = Param(
            m.regions,
            initialize=inputs.regional(
                "ACCREU", "labourprod_adapt_eff_max_effectiveness"
            ),
        )
        m.labourprod_adaptation_cost_param = Param(
            m.regions,
            initialize=inputs.regional("ACCREU", "labourprod_adapt_eff_cost_param"),
        )
        constraints.append(
            get_delayed_adaptation_constraint("labourprod_adaptation_costs")
        )
        constraints.extend(
            [
                # Adaptation effectiveness function
                RegionalEquation(
                    m.labourprod_adaptation_level,
                    lambda m, t, r: adaptation_effectiveness_fct(
                        m.labourprod_adaptation_costs_abs[t, r],
                        *effective_adaptation_curve(
                            m,
                            r,
                            m.labourprod_adaptation_max_effectiveness[r],
                            m.labourprod_adaptation_cost_param[r],
                            adaptation_calibration,
                        ),
                    ),
                ),
                # Adaptation costs as a fraction of GDP
                RegionalEquation(
                    m.labourprod_adaptation_costs,
                    lambda m, t, r: m.labourprod_adaptation_costs_abs[t, r]
                    / m.GDP_gross[t, r],
                ),
                # Residual damages after adaptation
                RegionalEquation(
                    m.labourprod_damage_costs,
                    lambda m, t, r: m.labourprod_damage_costs_gross[t, r]
                    * (1 - m.labourprod_adaptation_level[t, r]),
                ),
            ]
        )

        if adaptation_options.uses_analytical_adaptation:
            constraints.append(
                # Calculate analytically the optimal level of adaptation
                RegionalEquation(
                    m.labourprod_adaptation_costs_abs,
                    lambda m, t, r: optimal_adaptation_costs_fct(
                        m,
                        t,
                        m.labourprod_damage_costs_gross[t, r] * m.GDP_gross[t, r],
                        *effective_adaptation_curve(
                            m,
                            r,
                            m.labourprod_adaptation_max_effectiveness[r],
                            m.labourprod_adaptation_cost_param[r],
                            adaptation_calibration,
                        ),
                    ),
                )
            )

    if adaptation_type != "combined":
        ## Net damages (costs + negative benefits):

        m.labourprod_damage_costs_net = Var(
            m.t,
            m.regions,
            units=quant.unit("fraction_of_GDP"),
            doc="Sum of heat-related residual damages and cold-related benefits for labour productivity (net damages)",
        )

        constraints.append(
            RegionalEquation(
                m.labourprod_damage_costs_net,
                lambda m, t, r: m.labourprod_damage_costs[t, r]
                + m.labourprod_damage_costs_benefits[t, r],
            )
        )

    return constraints


def gross_dmg_fct_labourprod(m, t, r):
    """
    The heat-related gross damage costs are fitted using a linear function of global temperature, shifted to 0 at the start year.

    $$
        \\href{./#var__labourprod_damage_costs_gross}{\\text{gross damages}_{\\text{labourprod},t,r}}
        = (\\href{./#param__regional.ACCREU.labourprod_noadapt_ead_constant}{a_{r, \\text{heat}}} + \\href{./#param__regional.ACCREU.labourprod_noadapt_ead_linear}{b_{r, \\text{heat}}} \\cdot \\href{./#var__temperature}{T_t}) - (\\href{./#param__regional.ACCREU.labourprod_noadapt_ead_constant}{a_{r, \\text{heat}}} + \\href{./#param__regional.ACCREU.labourprod_noadapt_ead_linear}{b_{r, \\text{heat}}} \\cdot \\href{./#param__temperature.initial}{T_0}).
    $$
    """
    a = m.labourprod_damages_gross_constant[r]
    b = m.labourprod_damages_gross_linear[r]
    return dmg_fct_linear(m, t, a, b) * m.damage_scale_factor


def benefits_dmg_fct_labourprod(m, t, r):
    """
    The cold-related benefits of climate chnage are also fitted using a linear function of global temperature, and shifted to 0 at the start year.

    $$
        \\href{./#var__labourprod_damage_costs_benefits}{\\text{benefits}_{\\text{labourprod},t,r}}
        = (\\href{./#param__regional.ACCREU.labourprod_benefit_cdd_constant}{a_{r, \\text{cold}}} + \\href{./#param__regional.ACCREU.labourprod_benefit_cdd_linear}{b_{r, \\text{cold}}} \\cdot \\href{./#var__temperature}{T_t}) - (\\href{./#param__regional.ACCREU.labourprod_benefit_cdd_constant}{a_{r, \\text{cold}}} + \\href{./#param__regional.ACCREU.labourprod_benefit_cdd_linear}{b_{r, \\text{cold}}} \\cdot \\href{./#param__temperature.initial}{T_0}).
    $$
    """
    a = m.labourprod_damages_benefits_constant[r]
    b = m.labourprod_damages_benefits_linear[r]
    return dmg_fct_linear(m, t, a, b) * m.damage_scale_factor
