"""
Model equations and constraints:
Abatement costs
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    value,
    log,
    soft_min,
    NonNegativeReals,
    quant,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Abatement cost equations and constraints

    Necessary variables:
        m.abatement_costs

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    ### Technological learning

    # Learning by doing
    m.LBD_rate = Param()
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

    # Abatement costs and MAC
    m.abatement_costs = Var(
        m.t,
        m.regions,
        within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )
    m.area_under_MAC = Var(
        m.t,
        m.regions,
        within=NonNegativeReals,
        initialize=0,
        units=quant.unit("currency_unit"),
    )
    m.rel_abatement_costs = Var(
        m.t, m.regions, bounds=(0, 0.3), units=quant.unit("fraction_of_GDP")
    )
    m.MAC_gamma = Param()
    m.MAC_beta = Param()
    m.MAC_scaling_factor = Param(m.regions)  # Regional scaling of the MAC
    m.carbonprice = Var(
        m.t,
        m.regions,
        bounds=lambda m: (0, 1.5 * m.MAC_gamma),
        units=quant.unit("currency_unit/emissions_unit"),
    )
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: (
                    m.area_under_MAC[t, r]
                    if value(m.allow_trade)
                    else m.abatement_costs[t, r]
                )
                == AC(
                    m.relative_abatement[t, r],
                    m.learning_factor[t],
                    m.MAC_gamma,
                    m.MAC_beta,
                    m.MAC_scaling_factor[r],
                )
                * m.baseline[t, r],
                "abatement_costs",
            ),
            RegionalConstraint(
                lambda m, t, r: m.rel_abatement_costs[t, r]
                == m.abatement_costs[t, r] / m.GDP_gross[t, r],
                "rel_abatement_costs",
            ),
            RegionalConstraint(
                lambda m, t, r: m.carbonprice[t, r]
                == MAC(
                    m.relative_abatement[t, r],
                    m.learning_factor[t],
                    m.MAC_gamma,
                    m.MAC_beta,
                    m.MAC_scaling_factor[r],
                ),
                "carbonprice",
            ),
            RegionalInitConstraint(
                lambda m, r: m.carbonprice[0, r] == 0, "init_carbon_price"
            ),
        ]
    )

    # Manually set abatement level to zero until a certain year:
    m.no_abatement_zero_until_year = Param()
    constraints.extend(
        [
            RegionalConstraint(
                lambda m, t, r: m.relative_abatement[t, r] <= 1e-3
                if value(m.no_abatement_zero_until_year) is not False
                and t > 0
                and m.year(t) < m.no_abatement_zero_until_year
                else Constraint.Skip,
                "no_abatement_until_year_upperbound",
            ),
            RegionalConstraint(  # Purely here for numerical stability
                lambda m, t, r: m.relative_abatement[t, r] >= -1e-3
                if value(m.no_abatement_zero_until_year) is not False
                and t > 0
                and m.year(t) < m.no_abatement_zero_until_year
                else Constraint.Skip,
                "no_abatement_until_year_lowerbound",
            ),
        ]
    )

    # How are mitigation costs distributed over regions?
    m.allow_trade = Param()
    m.min_rel_payment_level = Param()
    m.max_rel_payment_level = Param()
    m.extra_paid_abatement = Var(
        m.t,
        m.regions,
        initialize=0.0,
        within=NonNegativeReals,
        units=quant.unit("currency_unit"),
    )
    m.extra_received_abatement = Var(
        m.t,
        m.regions,
        initialize=0.0,
        within=NonNegativeReals,
        units=quant.unit("currency_unit"),
    )
    constraints.extend(
        [
            # GlobalConstraint(
            #     lambda m, t: sum(m.abatement_costs[t, r] for r in m.regions)
            #     == sum(m.area_under_MAC[t, r] for r in m.regions)
            #     if m.allow_trade
            #     else Constraint.Skip
            # ),
            # RegionalConstraint(
            #     lambda m, t, r: m.abatement_costs[t, r]
            #     == m.paid_abatement_costs[t, r]
            #     + 0.01 * soft_min(m.paid_abatement_costs[t, r] - m.area_under_MAC[t, r])
            #     if m.allow_trade
            #     else Constraint.Skip
            # ),
            RegionalConstraint(
                lambda m, t, r: m.extra_paid_abatement[t, r]
                <= (m.max_rel_payment_level - 1)
                * m.area_under_MAC[t, r]  # TODO change " - 1"
                if m.allow_trade and value(m.max_rel_payment_level) is not False
                else Constraint.Skip
            ),
            RegionalConstraint(
                lambda m, t, r: m.extra_received_abatement[t, r]
                <= (1 - m.min_rel_payment_level)
                * m.area_under_MAC[t, r]  # TODO change "1 - "
                if m.allow_trade and value(m.min_rel_payment_level) is not False
                else Constraint.Skip
            ),
            RegionalConstraint(
                lambda m, t, r: m.abatement_costs[t, r]
                == m.area_under_MAC[t, r]
                + m.extra_paid_abatement[t, r]
                - m.extra_received_abatement[t, r]
                if m.allow_trade
                else Constraint.Skip,
                "abatement_is_real_costs_plus_extra_paid_minus_extra_received",
            ),
            GlobalConstraint(
                lambda m, t: sum(m.extra_paid_abatement[t, r] for r in m.regions)
                == sum(m.extra_received_abatement[t, r] for r in m.regions)
                if m.allow_trade
                else Constraint.Skip,
                "total_extra_abatement_paid_equals_total_extra_abatement_received",
            ),
            # GlobalConstraint(
            #     lambda m, t: sum(m.extra_paid_abatement[t, r] for r in m.regions) <= 0.1
            #     if m.allow_trade
            #     else Constraint.Skip,
            #     "limit_extra_abatement_transfers",
            # ),
            # RegionalConstraint(
            #     lambda m, t, r: m.extra_abatement_transfers[t, r]
            #     == soft_min(m.abatement_costs[t, r] - m.area_under_MAC[t, r], scale=0.2)
            #     if m.allow_trade
            #     else Constraint.Skip
            # ),
            # GlobalConstraint(
            #     lambda m, t: sum(m.extra_abatement_transfers[t, r] for r in m.regions)
            #     <= 0.135
            #     if m.allow_trade and m.year(t) <= 2050
            #     else Constraint.Skip
            # ),
        ]
    )

    # Keep track of relative global costs
    m.global_rel_abatement_costs = Var(m.t)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.global_rel_abatement_costs[t]
                == sum(m.abatement_costs[t, r] for r in m.regions)
                / sum(m.GDP_gross[t, r] for r in m.regions),
                "global_rel_abatement_costs",
            )
        ]
    )

    return constraints


#################
## Utils
#################


def MAC(a, factor, gamma, beta, MAC_scaling_factor):
    return gamma * factor * MAC_scaling_factor * a ** beta


def AC(a, factor, gamma, beta, MAC_scaling_factor):
    return gamma * factor * MAC_scaling_factor * a ** (beta + 1) / (beta + 1)
