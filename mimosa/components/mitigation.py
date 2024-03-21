"""
Model equations and constraints:
Mitigation costs
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    log,
    soft_min,
    quant,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """

    === ":material-chart-bell-curve-cumulative: Marginal Abatement Costs (MAC) and mitigation costs"

        :::mimosa.components.mitigation._get_mac_constraints

    === ":material-solar-power-variant-outline: Technological learning"

        :::mimosa.components.mitigation._get_learning_constraints

    """
    constraints = _get_mac_constraints(m) + _get_learning_constraints(m)

    return constraints


def _get_mac_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    In MIMOSA, the baseline emissions can be reduced by implementing a carbon price. This increases the price of
    carbon-intensive technologies relative to cleaner alternatives, which in turn leads to a reduction in emissions.

    ## Marginal Abatement Cost curve

    The carbon price required to reach a certain level of emission reduction is quantified by a Marginal Abatement
    Cost curve (MAC curve) and gives instantaneous reductions (emission reductions in a given year) relative to the
    baseline emissions. The MAC curve is defined by the following equation:

    :::mimosa.components.mitigation.MAC



    ## Parameters defined in this module
    - param::MAC_gamma
    - param::MAC_beta
    - param::MAC_scaling_factor
    - param::rel_mitigation_costs_min_level

    """

    constraints = []

    # Mitigation costs and MAC
    m.mitigation_costs = Var(
        m.t,
        m.regions,
        # within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )
    m.rel_mitigation_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.MAC_gamma = Param(doc="::economics.MAC.gamma")
    m.MAC_beta = Param(doc="::economics.MAC.beta")
    m.MAC_scaling_factor = Param(
        m.regions,
        doc=lambda params: f'regional::MAC.{params["economics"]["MAC"]["regional calibration factor"]}',
    )  # Regional scaling of the MAC
    m.carbonprice = Var(
        m.t,
        m.regions,
        bounds=lambda m: (0, 2 * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )
    m.rel_mitigation_costs_min_level = Param(
        doc="::economics.MAC.rel_mitigation_costs_min_level"
    )
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.rel_mitigation_costs[t, r]
                == m.mitigation_costs[t, r] / m.GDP_gross[t, r],
                "rel_mitigation_costs",
                doc="$$ \\text{rel_mitigation_costs}_{t,r} = \\frac{\\text{mitigation_costs}_{t,r}}{\\text{GDP_gross}_{t,r}} $$",
            ),
            RegionalConstraint(
                lambda m, t, r: m.rel_mitigation_costs[t, r]
                >= (m.rel_mitigation_costs_min_level if t > 0 else 0.0),
                "rel_mitigation_costs_non_negative",
            ),
            RegionalConstraint(
                lambda m, t, r: m.carbonprice[t, r]
                == MAC(m.relative_abatement[t, r], m, t, r),
                "carbonprice",
            ),
            RegionalInitConstraint(
                lambda m, r: m.carbonprice[0, r] == 0, "init_carbon_price"
            ),
        ]
    )

    # Keep track of relative global costs
    m.global_rel_mitigation_costs = Var(m.t)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.global_rel_mitigation_costs[t]
                == sum(m.mitigation_costs[t, r] for r in m.regions)
                / sum(m.GDP_gross[t, r] for r in m.regions),
                "global_rel_mitigation_costs",
            )
        ]
    )

    # Calculate average global emission reduction per cost unit
    # and average cost per unit emission reduction

    m.global_emission_reduction_per_cost_unit = Var(
        m.t, units=quant.unit("emissionsrate_unit / currency_unit")
    )
    m.global_cost_per_emission_reduction_unit = Var(
        m.t, units=quant.unit("currency_unit / emissionsrate_unit")
    )
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    m.global_emission_reduction_per_cost_unit[t]
                    == sum(m.regional_emission_reduction[t, r] for r in m.regions)
                    / soft_min(sum(m.mitigation_costs[t, r] for r in m.regions))
                    if t > 0
                    else Constraint.Skip
                ),
                "global_emission_reduction_per_cost_unit",
            ),
            GlobalConstraint(
                lambda m, t: (
                    m.global_cost_per_emission_reduction_unit[t]
                    == sum(m.mitigation_costs[t, r] for r in m.regions)
                    / soft_min(
                        sum(m.regional_emission_reduction[t, r] for r in m.regions)
                    )
                    if t > 0
                    else Constraint.Skip
                ),
                "global_cost_per_emission_reduction_unit",
            ),
        ]
    )

    return constraints


def _get_learning_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    ## Learning by doing

    ## Learning over time

    """
    constraints = []

    ### Technological learning

    # Learning by doing
    m.LBD_rate = Param(doc="::economics.MAC.rho")
    m.log_LBD_rate = Param(initialize=log(m.LBD_rate) / log(2))
    m.LBD_scaling = Param()
    m.LBD_factor = Var(m.t)  # , bounds=(0,1), initialize=1)
    constraints.append(
        GlobalConstraint(
            lambda m, t: m.LBD_factor[t]
            == soft_min(
                (
                    m.baseline_cumulative_global(m, m.year(0), m.year(t))
                    - m.cumulative_emissions[t]
                )
                / m.LBD_scaling
                + 1.0
            )
            ** m.log_LBD_rate,
            name="LBD",
        )
    )

    # Learning over time and total learning factor
    m.LOT_rate = Param()
    m.LOT_factor = Var(m.t)
    m.learning_factor = Var(m.t)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.LOT_factor[t] == 1 / (1 + m.LOT_rate) ** t, "LOT"
            ),
            GlobalConstraint(
                lambda m, t: m.learning_factor[t]
                == (m.LBD_factor[t] * m.LOT_factor[t]),
                "learning",
            ),
        ]
    )

    return constraints


#################
## Utils
#################


def MAC(a, m, t, r):
    """
    $$
    \\text{carbon price}_{t,r} = \\text{factor}_{t,r} \\cdot \\gamma \\cdot \\left(\\text{rel. mitigation}_{t,r}\\right)^{\\beta},
    $$

    where the MAC is scaled by the following time and region dependent factor:
    $$
    \\text{factor}_{t,r} = \\text{learning factor}_t \\cdot \\text{regional scaling factor}_r
    $$

    The regional scaling factor transforms the global MAC into a regional MAC:


    ``` plotly
    {"file_path": "./assets/plots/MAC_kappa_rel_abatement_0.75_2050.json"}
    ```

    The values of this regional scaling factor are calibrated using SSP2 MAC curves from the TIMER model (the energy
    submodule of IMAGE). By comparing the carbon price per region required to reach 75% CO<sub>2</sub> reduction in 2050 compared to baseline,
    relative to the world average, we obtain a scaling factor for the MAC.
    """
    factor = m.learning_factor[t] * m.MAC_scaling_factor[r]
    return factor * m.MAC_gamma * a**m.MAC_beta


def AC(a, m, t, r):
    factor = m.learning_factor[t] * m.MAC_scaling_factor[r]
    return factor * m.MAC_gamma * a ** (m.MAC_beta + 1) / (m.MAC_beta + 1)
