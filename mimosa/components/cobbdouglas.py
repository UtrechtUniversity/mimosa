"""
Model equations and constraints:
Economics and Cobb-Douglas
"""

from typing import Sequence
from mimosa.common import (
    ConcreteModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    value,
    soft_min,
    economics,
    quant,
)

from mimosa.core.model_inputs import ModelInputs


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""
    # Economic module and production function

    ## Gross and net GDP

    The core of the model is the economic module, detailing how GDP, investments and
    consumptions vary over time. We use a traditional Cobb-Douglas production function. This means
    that the gross GDP is calculated by:

    :::mimosa.common.economics.calc_GDP

    The net GDP is then calculated by subtracting the damages and
    mitigation costs from the gross GDP. The `_abs` variables are used here because the amounts
    subtracted from GDP must be in currency units.

    $$
    \begin{align}
    \href{./#var__GDP_net}{\text{GDP}_{\text{net},t,r}} =\ & \href{./#var__GDP_gross}{\text{GDP}_{\text{gross},t,r}} \cdot (1 - \href{./#var__damage_costs}{\text{damage costs}_{t,r}}) \\
    &\ \ \ - \href{./#var__mitigation_costs_abs}{\text{mitigation costs abs}_{t,r}} - \href{./#var__financialtransfer_globaldamagepool::financial_transfer_abs}{\text{financial transfer abs}_{t,r}}
    \end{align}
    $$

    The last term represents optional financial transfers to compensate regions for damage
    costs. By default this term is always 0 (see [Financial transfers](financialtransfers.md)).

    ## Investments and consumption

    This net GDP is then split in a part of investments ($\href{./#var__investments}{I_t}$) and a part of consumption ($\href{./#var__consumption}{C_t}$), according to a fixed savings rate ($\href{./#param__economics.GDP.savings rate}{\text{sr}}$):

    $$ \href{./#var__investments}{I_{t,r}} = \href{./#param__economics.GDP.savings rate}{\text{sr}} \cdot \href{./#var__GDP_net}{\text{GDP}_{\text{net},t,r}}, $$

    $$ \href{./#var__consumption}{C_{t,r}} = (1 - \href{./#param__economics.GDP.savings rate}{\text{sr}}) \cdot \href{./#var__GDP_net}{\text{GDP}_{\text{net},t,r}}. $$

    Consumption is physical consumption. Monetised non-market damages, such as mortality,
    are deducted separately in the welfare calculation.

    ## Capital stock

    The capital stock $\href{./#var__capital_stock}{K_t}$ grows over time according to the investments and the depreciation of the capital stock:

    $$ \href{./#var__capital_stock}{K_{t,r}} = \href{./#var__capital_stock}{K_{t-1,r}} + \Delta t \cdot \frac{\partial \href{./#var__capital_stock}{K_{t,r}}}{\partial t}, $$

    with the change in capital stock calculated by:

    :::mimosa.common.economics.calc_dKdt

    Since this only gives the change in capital stock, we need to add the initial capital stock to get the actual capital stock.
    This is calculated as a region-dependent multiple of the initial GDP:

    $$ \href{./#var__capital_stock}{K_{t=0,r}} = \href{./#param__regional.economics.init_capital_factor}{\text{init_capitalstock_factor}_r} \cdot \href{./#param__timeandregional.baseline_GDP}{\text{GDP}_{t=0,r}}. $$

    The [regional initial capital stock factors](#param__regional.economics.init_capital_factor) are calibrated from capital-stock-to-GDP ratios in
    the [IMF Investment and Capital Stock Dataset](https://data.imf.org/en/Datasets/ICSD).
    ``` plotly
    {"file_path": "./assets/plots/economics_init_capital_factor.json"}
    ```

    ## Parameters defined in this module
    - param::init_capitalstock_factor
    - param::alpha
    - param::dk
    - param::sr
    - param::ignore_damages



    """
    constraints = []
    m.init_capitalstock_factor = Param(
        m.regions,
        units=quant.unit("dimensionless"),
        initialize=inputs.regional("economics", "init_capital_factor"),
    )
    m.capital_stock = Var(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.init_capitalstock_factor[r] * m.baseline_GDP[t, r],
        units=quant.unit("currency_unit"),
        doc="Regional stock of productive capital. Increases through investment and decreases through depreciation; used in the Cobb-Douglas production function.",
    )

    # Parameters
    m.alpha = Param(initialize=inputs.config("economics.GDP.alpha"))
    m.dk = Param(initialize=inputs.config("economics.GDP.depreciation of capital"))
    m.sr = Param(initialize=inputs.config("economics.GDP.savings rate"))

    m.GDP_gross = Var(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.baseline_GDP[0, r],
        units=quant.unit("currency_unit"),
        doc="Regional gross GDP from the Cobb-Douglas production function, before deducting damages, adaptation costs, mitigation costs, and financial transfers.",
    )
    m.global_GDP_gross = Var(
        m.t,
        initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
        doc="Global gross GDP, calculated as the sum of regional gross GDP.",
    )
    m.GDP_net = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        initialize=lambda m, t, r: m.baseline_GDP[0, r],
        doc="Regional net GDP available for investment and consumption after mitigation costs, financial transfers, and any included damage and adaptation costs.",
    )
    m.global_GDP_net = Var(
        m.t,
        initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
        doc="Global net GDP, calculated as the sum of regional net GDP.",
    )
    m.investments = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        doc="Regional investment in productive capital, calculated as the fixed savings rate times net GDP.",
    )
    m.consumption = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        doc="Regional physical consumption, equal to net GDP minus investment.",
    )

    m.ignore_damages = Param(
        initialize=inputs.config("economics.damages.ignore damages")
    )

    m.TFP = Param(m.t, m.regions, initialize=economics.get_TFP_value)

    # Cobb-Douglas, GDP, investments, capital and consumption
    constraints.extend(
        [
            RegionalEquation(
                m.capital_stock,
                lambda m, t, r: (
                    m.capital_stock[t - 1, r]
                    + m.period_length[t]
                    * economics.calc_dKdt(
                        m.capital_stock[t - 1, r],
                        m.dk,
                        m.investments[t - 1, r],
                        m.period_length[t],
                    )
                    if t > 0
                    else m.init_capitalstock_factor[r] * m.baseline_GDP[0, r]
                ),
            ),
            RegionalEquation(
                m.GDP_gross,
                lambda m, t, r: (
                    economics.calc_GDP(
                        m.TFP[t, r],
                        m.population[t, r],
                        soft_min(m.capital_stock[t, r], scale=10),
                        m.alpha,
                    )
                    if t > 0
                    else m.baseline_GDP[0, r]
                ),
            ),
            GlobalEquation(
                m.global_GDP_gross,
                lambda m, t: sum(m.GDP_gross[t, r] for r in m.regions),
            ),
            RegionalEquation(
                m.GDP_net,
                lambda m, t, r: (
                    m.GDP_gross[t, r]
                    * (
                        1
                        - (
                            (m.damage_costs[t, r] + m.adaptation_costs[t, r])
                            if not value(m.ignore_damages)
                            else 0
                        )
                    )
                    - m.mitigation_costs_abs[t, r]
                    - m.financial_transfer_abs[t, r]
                ),
            ),
            GlobalEquation(
                m.global_GDP_net,
                lambda m, t: sum(m.GDP_net[t, r] for r in m.regions),
            ),
            RegionalEquation(
                m.investments,
                lambda m, t, r: m.sr * m.GDP_net[t, r],
            ),
            RegionalEquation(
                m.consumption,
                lambda m, t, r: (1 - m.sr) * m.GDP_net[t, r],
            ),
        ]
    )

    # GDP loss: takes into account indirect effects of reduced GDP growth due to damages and mitigation costs
    m.GDP_loss = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_baseline_GDP"),
        initialize=0,
        doc="Regional GDP loss relative to the baseline, calculated as baseline GDP minus net GDP, divided by baseline GDP. Includes direct costs and indirect effects on economic growth.",
    )
    m.global_GDP_loss = Var(
        m.t,
        units=quant.unit("fraction_of_baseline_GDP"),
        initialize=0,
        doc="Global GDP loss relative to the baseline, calculated as global baseline GDP minus global net GDP, divided by global baseline GDP.",
    )

    m.total_direct_costs_abs = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        initialize=0,
        doc="Total regional direct costs in currency units: the sum of mitigation costs, damage costs, and adaptation costs.",
    )
    m.indirect_costs = Var(
        m.t,
        m.regions,
        units=quant.unit("fraction_of_baseline_GDP"),
        initialize=0,
        doc="Regional GDP loss beyond direct costs, expressed as a fraction of baseline GDP. Includes effects of reduced capital accumulation.",
    )
    m.global_indirect_costs = Var(
        m.t,
        units=quant.unit("fraction_of_baseline_GDP"),
        initialize=0,
        doc="Global GDP loss beyond direct costs, calculated as global GDP loss minus total direct costs divided by global baseline GDP.",
    )

    constraints.extend(
        [
            RegionalEquation(
                m.GDP_loss,
                lambda m, t, r: (
                    (m.baseline_GDP[t, r] - m.GDP_net[t, r]) / m.baseline_GDP[t, r]
                ),
            ),
            GlobalEquation(
                m.global_GDP_loss,
                lambda m, t: (
                    (m.global_baseline_GDP[t] - m.global_GDP_net[t])
                    / m.global_baseline_GDP[t]
                ),
            ),
            RegionalEquation(
                m.total_direct_costs_abs,
                lambda m, t, r: (
                    m.mitigation_costs_abs[t, r]
                    + m.damage_costs_abs[t, r]
                    + m.adaptation_costs_abs[t, r]
                ),
            ),
            RegionalEquation(
                m.indirect_costs,
                lambda m, t, r: (
                    m.GDP_loss[t, r]
                    - (m.total_direct_costs_abs[t, r] / m.baseline_GDP[t, r])
                ),
            ),
            GlobalEquation(
                m.global_indirect_costs,
                lambda m, t: (
                    m.global_GDP_loss[t]
                    - (
                        sum(m.total_direct_costs_abs[t, r] for r in m.regions)
                        / m.global_baseline_GDP[t]
                    )
                ),
            ),
        ]
    )

    return constraints
