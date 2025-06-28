"""
Model equations and constraints:
Economics and Cobb-Douglas
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
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


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    # Economic module and production function

    ## Gross and net GDP

    The core of the model is the economic module, detailing how GDP, investments and
    consumptions vary over time. We use a traditional Cobb-Douglas production function. This means
    that the gross GDP is calculated by:

    :::mimosa.common.economics.calc_GDP

    The net GDP is then calculated by subtracting the damages and
    mitigation costs from the gross GDP. *(Note that in MIMOSA, the damages are expressed as a fraction of the gross GDP,
    whereas the mitigation costs are expressed in absolute terms.)*

    $$
    \\begin{align}
    \\text{GDP}_{\\text{net},t,r} =\\ & \\text{GDP}_{\\text{gross},t,r} \\cdot (1 - \\text{damage costs}_{t,r}) \\\\
    &\\ \\ \\ - \\text{mitigation costs}_{t,r} - \\text{financial transf.}_{t,r}
    \\end{align}
    $$

    The last term represents optional financial transfers to compensate regions for damage
    costs. By default this term is always 0 (see [Financial transfers](financialtransfers.md)).

    ## Investments and consumption

    This net GDP is then split in a part of investments ($I_t$) and a part of consumption ($C_t$), according to a fixed savings rate ($\\text{sr}$):

    $$ I_{t,r} = \\text{sr} \\cdot \\text{GDP}_{\\text{net},t,r}, $$

    $$ C_{t,r} = (1 - \\text{sr}) \\cdot \\text{GDP}_{\\text{net},t,r}. $$

    ## Capital stock

    The capital stock $K_t$ grows over time according to the investments and the depreciation of the capital stock:

    $$ K_{t,r} = K_{t-1,r} + \\Delta t \\cdot \\frac{\\partial K_{t,r}}{\\partial t}, $$

    with the change in capital stock calculated by:

    :::mimosa.common.economics.calc_dKdt

    Since this only gives the change in capital stock, we need to add the initial capital stock to get the actual capital stock.
    This is calculated as a region-dependent multiple of the initial GDP:

    $$ K_{t=0,r} = \\text{init_capitalstock_factor}_r \\cdot \\text{GDP}_{t=0,r}. $$

    The initial capital stock factor is a calibration factor to obtain the initial capital stock. TODO: Source (IMF)
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
        doc="regional::economics.init_capital_factor",
    )
    m.capital_stock = Var(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.init_capitalstock_factor[r] * m.baseline_GDP[t, r],
        units=quant.unit("currency_unit"),
    )

    # Parameters
    m.alpha = Param(doc="::economics.GDP.alpha")
    m.dk = Param(doc="::economics.GDP.depreciation of capital")
    m.sr = Param(doc="::economics.GDP.savings rate")

    m.GDP_gross = Var(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.baseline_GDP[0, r],
        units=quant.unit("currency_unit"),
    )
    m.global_GDP_gross = Var(
        m.t,
        initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
    )
    m.GDP_net = Var(
        m.t,
        m.regions,
        units=quant.unit("currency_unit"),
        initialize=lambda m, t, r: m.baseline_GDP[0, r],
    )
    m.global_GDP_net = Var(
        m.t,
        initialize=lambda m, t: sum(m.baseline_GDP[t, r] for r in m.regions),
        units=quant.unit("currency_unit"),
    )
    m.investments = Var(m.t, m.regions, units=quant.unit("currency_unit"))
    m.consumption = Var(m.t, m.regions, units=quant.unit("currency_unit"))

    m.ignore_damages = Param(doc="::economics.damages.ignore damages")

    m.TFP = Param(m.t, m.regions, initialize=economics.get_TFP_value)

    # Cobb-Douglas, GDP, investments, capital and consumption
    constraints.extend(
        [
            RegionalEquation(
                m.capital_stock,
                lambda m, t, r: (
                    m.capital_stock[t - 1, r]
                    + m.dt
                    * economics.calc_dKdt(
                        m.capital_stock[t - 1, r], m.dk, m.investments[t - 1, r], m.dt
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
                    * (1 - (m.damage_costs[t, r] if not value(m.ignore_damages) else 0))
                    - m.mitigation_costs[t, r]
                    - m.financial_transfer[t, r]
                ),
            ),
            GlobalEquation(
                m.global_GDP_net,
                lambda m, t: sum(m.GDP_net[t, r] for r in m.regions),
            ),
            RegionalEquation(
                m.investments,
                lambda m, t, r: (m.sr * m.GDP_net[t, r]),
            ),
            RegionalEquation(
                m.consumption,
                lambda m, t, r: ((1 - m.sr) * m.GDP_net[t, r]),
            ),
        ]
    )

    return constraints
