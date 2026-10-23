"""
Model equations and constraints:
Utility and global welfare
"""

from typing import Sequence

from mimosa.common import (
    ConcreteModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
)
from .utility_fct import calc_utility

from mimosa.core.model_inputs import ModelInputs


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    r"""

    <h3>Cost-minimising setting</h3>

    In cost-minimising setting, the global per-capita consumption is first calculated before
    applying the utility function. This means that costs are weighted equally across regions,
    regardless of the regional per capita consumption. As a consequence, this setting leads to
    uniform carbon prices across regions. This is quantitatively similar to using Negishi weights.

    ???+ info "Difference with welfare-loss-minimising setting"
        In the welfare-loss-minimising setting, the utility function is applied to the regional
        per capita consumption values, and the regional utilities are then summed up to get the
        global welfare. This means that costs (from mitigation or damages) have a larger weight in
        the final welfare in poorer regions than in richer regions.


    <h3>Equations</h3>

    First, aggregate consumption after deducting non-market damages, and population:

    $$ \widehat{C}_{t} = \sum_r \left(\href{./#var__welfare_cost_minimising::consumption}{C_{t,r}} - \href{./#var__accreu_sectoral::non_market_damage_costs_abs}{D^{\mathrm{NM}}_{t,r}}\right), $$

    $$ \widehat{L}_{t} = \sum_r \href{./#param__timeandregional.population}{L_{t,r}}. $$

    These are used to calculate the global utility:

    $$ \href{./#var__welfare_cost_minimising::global_welfare}{W_t} = \widehat{L}_t \cdot \text{utility}\left( \widehat{C}_{t}, \widehat{L}_{t} \right) $$

    <h3>Utility function</h3>
    :::mimosa.components.welfare.utility_fct.calc_utility


    <h3>Parameters defined in this module</h3>
    - param::elasmu

    """
    constraints = []

    # Parameters
    m.elasmu = Param(initialize=inputs.config("economics.elasmu"))

    m.utility = Var(
        m.t,
        m.regions,
        initialize=10,
        doc="Regional consumption per person after deducting monetised non-market damages, reported as the utility variable in the cost-minimising setting.",
    )
    m.global_welfare = Var(
        m.t,
        doc="Undiscounted global welfare, calculated by applying the utility function to global per-capita consumption after non-market damages and multiplying by global population.",
    )

    constraints.extend(
        [
            RegionalEquation(
                m.utility,
                lambda m, t, r: (
                    m.consumption[t, r] - m.non_market_damage_costs_abs[t, r]
                )
                / m.population[t, r],
            ),
            GlobalEquation(
                m.global_welfare,
                lambda m, t: m.global_population[t]
                * calc_utility(
                    sum(
                        m.consumption[t, r] - m.non_market_damage_costs_abs[t, r]
                        for r in m.regions
                    ),
                    sum(m.population[t, r] for r in m.regions),
                    m.elasmu,
                ),
            ),
        ]
    )

    return constraints
