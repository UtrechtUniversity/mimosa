import numpy as np
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    economics,
    value,
    exp,
    quant,
    soft_min,
    soft_max,
)
from mimosa.components.damages.coacch import damage_fct
from mimosa.components.mitigation import AC, MAC
from mimosa.components.sealevelrise import (
    slr_gis,
    slr_gsic,
    slr_thermal_expansion,
    slr_thermal_expansion_init,
)
from mimosa.components.welfare.utility_fct import calc_utility

from inspect import signature


# baseline
# regional_emissions
# regional_emission_reduction
# global_emissions
# cumulative_emissions
# emission_relative_cumulative
# temperature

# capital_stock
# GDP_gross
# global_GDP_gross

# slr_thermal
# slr_cumgis
# slr_cumgsic
# total_SLR
# damage_costs_slr
# damage_costs_nonslr
# damage_costs
# damage_relative_global

# LOT_factor
# LBD_factor
# learning_factor

# carbonprice
# mitigation_costs
# rel_mitigation_costs
# area_under_MAC
# global_cost_per_emission_reduction_unit
# global_emission_reduction_per_cost_unit
# global_rel_mitigation_costs

# GDP_net
# investments
# consumption

# utility
# yearly_welfare
# NPV

expressions_rhs = {
    "baseline": lambda m, t, r: (
        (
            m.baseline_carbon_intensity[t, r]
            * (m.GDP_net[t - 1, r] if t > 1 else m.GDP_gross[t, r])
        )
        if value(m.use_carbon_intensity_for_baseline)
        else m.baseline_emissions[t, r]
    ),
    "regional_emissions": lambda m, t, r: (
        (1 - m.relative_abatement[t, r])
        * (
            m.baseline[t, r]
            if value(m.use_carbon_intensity_for_baseline)
            else m.baseline_emissions[t, r]
        )
        if t > 0
        else m.baseline_emissions[0, r]
    ),
    "regional_emission_reduction": lambda m, t, r: (
        m.baseline[t, r] - m.regional_emissions[t, r]
    ),
    "global_emissions": lambda m, t: (
        sum(m.regional_emissions[t, r] for r in m.regions)
        if t > 0
        else sum(m.baseline_emissions[0, r] for r in m.regions)
    ),
    "cumulative_emissions": lambda m, t: (
        m.cumulative_emissions[t - 1]
        + (
            (m.dt * (m.global_emissions[t] + m.global_emissions[t - 1]) / 2)
            if value(m.cumulative_emissions_trapz)
            else (m.dt * m.global_emissions[t])
        )
        if t > 0
        else 0
    ),
    "emission_relative_cumulative": lambda m, t: (
        m.cumulative_emissions[t] / m.cumulative_global_baseline_emissions[t]
        if t > 0
        else 1
    ),
    "temperature": lambda m, t: (
        m.T0 + m.TCRE * m.cumulative_emissions[t] if t > 0 else m.T0
    ),
    "capital_stock": lambda m, t, r: (
        m.capital_stock[t - 1, r]
        + m.dt
        * economics.calc_dKdt(
            m.capital_stock[t, r], m.dk, m.investments[t - 1, r], m.dt
        )
        if t > 0
        else m.init_capitalstock_factor[r] * m.baseline_GDP[0, r]
    ),
    "GDP_gross": lambda m, t, r: (
        economics.calc_GDP(
            m.TFP[t, r],
            m.population[t, r],
            soft_min(m.capital_stock[t, r], scale=10),
            m.alpha,
        )
        if t > 0
        else m.baseline_GDP[0, r]
    ),
    "global_GDP_gross": lambda m, t: (sum(m.GDP_gross[t, r] for r in m.regions)),
    "slr_thermal": lambda m, t: (
        slr_thermal_expansion(m.slr_thermal[t - 1], m.temperature[t - 1], m)
        if t > 0
        else slr_thermal_expansion_init(m)
    ),
    "slr_cumgsic": lambda m, t: (
        slr_gsic(m.slr_cumgsic[t - 1], m.temperature[t - 1], m) if t > 0 else 0.015
    ),
    "slr_cumgis": lambda m, t: (
        slr_gis(m.slr_cumgis[t - 1], m.temperature[t - 1], m) if t > 0 else 0.006
    ),
    "total_SLR": lambda m, t: (m.slr_thermal[t] + m.slr_cumgsic[t] + m.slr_cumgis[t]),
    "damage_costs_non_slr": lambda m, t, r: (
        m.damage_scale_factor
        * damage_fct(m.temperature[t] - 0.6, m.T0 - 0.6, m, r, is_slr=False)
    ),
    "damage_costs_slr": lambda m, t, r: (
        m.damage_scale_factor
        * damage_fct(m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True)
    ),
    "damage_costs": lambda m, t, r: (
        m.damage_costs_non_slr[t, r] + m.damage_costs_slr[t, r]
    ),
    "damage_relative_global": lambda m, t: (
        sum(m.damage_costs[t, r] * m.GDP_gross[t, r] for r in m.regions)
        / m.global_GDP_gross[t]
    ),
    "LBD_factor": lambda m, t: (
        soft_min(
            (
                m.cumulative_global_baseline_emissions[t - 1]
                - m.cumulative_emissions[t - 1]  # Now changed to t-1, check
            )
            / m.LBD_scaling
            + 1.0
        )
        ** m.log_LBD_rate
        if t > 0
        else 1.0
    ),
    "LOT_factor": lambda m, t: (1 / (1 + m.LOT_rate) ** t),
    "learning_factor": lambda m, t: (m.LBD_factor[t] * m.LOT_factor[t]),
    "carbonprice": lambda m, t, r: (
        MAC(m.relative_abatement[t, r], m, t, r) if t > 0 else 0
    ),
    "mitigation_costs": lambda m, t, r: (
        AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r]
        + m.import_export_mitigation_cost_balance[t, r]
    ),
    "rel_mitigation_costs": lambda m, t, r: (
        m.mitigation_costs[t, r] / m.GDP_gross[t, r]
    ),
    "area_under_MAC": lambda m, t, r: (
        AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r]
    ),
    "global_cost_per_emission_reduction_unit": lambda m, t: (
        sum(m.mitigation_costs[t, r] for r in m.regions)
        / soft_min(sum(m.regional_emission_reduction[t, r] for r in m.regions))
        if t > 0
        else 0
    ),
    "global_emission_reduction_per_cost_unit": lambda m, t: (
        sum(m.regional_emission_reduction[t, r] for r in m.regions)
        / soft_min(sum(m.mitigation_costs[t, r] for r in m.regions))
        if t > 0
        else 0
    ),
    "global_rel_mitigation_costs": lambda m, t: (
        sum(m.mitigation_costs[t, r] for r in m.regions) / m.global_GDP_gross[t]
    ),
    "GDP_net": lambda m, t, r: (
        m.GDP_gross[t, r]
        * (1 - (m.damage_costs[t, r] if not value(m.ignore_damages) else 0))
        - m.mitigation_costs[t, r]
        - m.financial_transfer[t, r]
    ),
    "investments": lambda m, t, r: (m.sr * m.GDP_net[t, r]),
    "consumption": lambda m, t, r: ((1 - m.sr) * m.GDP_net[t, r]),
    "utility": lambda m, t, r: (
        calc_utility(m.consumption[t, r], m.population[t, r], m.elasmu)
    ),
    "yearly_welfare": lambda m, t: (
        sum(m.population[t, r] * m.utility[t, r] for r in m.regions)
    ),
    "NPV": lambda m, t: (
        m.NPV[t - 1]
        + m.dt * exp(-m.PRTP * (m.year(t) - m.beginyear)) * m.yearly_welfare[t]
        if t > 0
        else 0
    ),
}


def get_all_constraints(m: AbstractModel):

    constraints = []
    for var_lhs, expr_rhs in expressions_rhs.items():
        # Check if it is a regional or global constraint using len(signature(expr_rhs).parameters)
        num_params = len(signature(expr_rhs).parameters)
        if num_params == 3:
            constraints.append(
                RegionalConstraint(
                    lambda m, t, r, expr_rhs=expr_rhs, var_lhs=var_lhs: getattr(
                        m, var_lhs
                    )[t, r]
                    == expr_rhs(m, t, r),
                    name=var_lhs,
                )
            )
        elif num_params == 2:
            constraints.append(
                GlobalConstraint(
                    lambda m, t, expr_rhs=expr_rhs, var_lhs=var_lhs: getattr(
                        m, var_lhs
                    )[t]
                    == expr_rhs(m, t),
                    name=var_lhs,
                )
            )
        else:
            print(f"Unknown number of parameters for {var_lhs}")

    constraints_vars = [
        RegionalConstraint(
            lambda m, t, r: (
                (
                    m.baseline[t, r]
                    == m.baseline_carbon_intensity[t, r]
                    * (m.GDP_net[t - 1, r] if t > 1 else m.GDP_gross[t, r])
                )
                if value(m.use_carbon_intensity_for_baseline)
                else (m.baseline[t, r] == m.baseline_emissions[t, r])
            ),
            name="baseline_emissions",
        ),
        RegionalConstraint(
            lambda m, t, r: (
                m.regional_emissions[t, r]
                == (1 - m.relative_abatement[t, r])
                * (
                    m.baseline[t, r]
                    if value(m.use_carbon_intensity_for_baseline)
                    else m.baseline_emissions[t, r]
                    # Note: this should simply be m.baseline[t,r], but this is numerically less stable
                    # than m.baseline_emissions[t, r] whenever baseline intensity
                    # is used instead of baseline emissions. In fact, m.baseline_emissions[t, r]
                    # is just a fixed number, whereas m.baseline[t,r] is a variable depending on
                    # GDP.
                )
                if t > 0
                else Constraint.Skip
            ),
            "regional_abatement",
        ),
        RegionalInitConstraint(
            lambda m, r: m.regional_emissions[0, r] == m.baseline_emissions[0, r]
        ),
        RegionalConstraint(
            lambda m, t, r: m.regional_emission_reduction[t, r]
            == m.baseline[t, r] - m.regional_emissions[t, r],
            "regional_emission_reduction",
        ),
        # Global emissions (sum from regional emissions)
        GlobalConstraint(
            lambda m, t: (
                m.global_emissions[t]
                == sum(m.regional_emissions[t, r] for r in m.regions)
                if t > 0
                else Constraint.Skip
            ),
            "global_emissions",
        ),
        GlobalInitConstraint(
            lambda m: m.global_emissions[0]
            == sum(m.baseline_emissions[0, r] for r in m.regions),
            "global_emissions_init",
        ),
        GlobalInitConstraint(lambda m: m.cumulative_emissions[0] == 0),
        GlobalConstraint(
            lambda m, t: (
                m.cumulative_emissions[t]
                == m.cumulative_emissions[t - 1]
                + (
                    (m.dt * (m.global_emissions[t] + m.global_emissions[t - 1]) / 2)
                    if value(m.cumulative_emissions_trapz)
                    else (m.dt * m.global_emissions[t])
                )
                if t > 0
                else Constraint.Skip
            ),
            "cumulative_emissions",
        ),
        GlobalConstraint(
            lambda m, t: (
                (
                    m.emission_relative_cumulative[t]
                    == m.cumulative_emissions[t]
                    / m.cumulative_global_baseline_emissions[t]
                )
                if t > 0
                else Constraint.Skip
            ),
            name="relative_cumulative_emissions",
        ),
        GlobalInitConstraint(lambda m: m.emission_relative_cumulative[0] == 1),
        GlobalConstraint(
            lambda m, t: m.temperature[t] == m.T0 + m.TCRE * m.cumulative_emissions[t],
            "temperature",
        ),
        GlobalInitConstraint(lambda m: m.temperature[0] == m.T0),
        GlobalConstraint(
            lambda m, t: (
                m.temperature[t] <= m.temperature_target
                if (m.year(t) >= 2100 and value(m.temperature_target) is not False)
                else Constraint.Skip
            ),
            name="temperature_target",
        ),
        ####################################
        ####################################
        RegionalConstraint(
            lambda m, t, r: (  # TODO: Circular dependency
                (
                    m.capital_stock[t, r]
                    == m.capital_stock[t - 1, r]
                    + m.dt
                    * economics.calc_dKdt(
                        m.capital_stock[t, r], m.dk, m.investments[t - 1, r], m.dt
                    )
                )
                if t > 0
                else Constraint.Skip
            ),
            "capital_stock",
        ),
        RegionalInitConstraint(
            lambda m, r: m.capital_stock[0, r]
            == m.init_capitalstock_factor[r] * m.baseline_GDP[0, r]
        ),
        RegionalInitConstraint(
            lambda m, r: m.GDP_gross[0, r] == m.baseline_GDP[0, r], "GDP_gross_init"
        ),
        RegionalConstraint(
            lambda m, t, r: (
                m.GDP_gross[t, r]
                == economics.calc_GDP(
                    m.TFP[t, r],
                    m.population[t, r],
                    soft_min(m.capital_stock[t, r], scale=10),
                    m.alpha,
                )
                if t > 0
                else Constraint.Skip
            ),
            "GDP_gross",
        ),
        GlobalConstraint(
            lambda m, t: (
                m.global_GDP_gross[t] == sum(m.GDP_gross[t, r] for r in m.regions)
            ),
            "global_GDP_gross",
        ),
        ####################################
        ####################################
        GlobalConstraint(
            lambda m, t: (
                m.slr_thermal[t]
                == slr_thermal_expansion(m.slr_thermal[t - 1], m.temperature[t - 1], m)
                if t > 0
                else Constraint.Skip
            ),
            name="SLR_thermal",
        ),
        GlobalInitConstraint(
            lambda m: m.slr_thermal[0] == slr_thermal_expansion_init(m)
        ),
        # GSIC
        GlobalConstraint(
            lambda m, t: (
                m.slr_cumgsic[t]
                == slr_gsic(m.slr_cumgsic[t - 1], m.temperature[t - 1], m)
                if t > 0
                else Constraint.Skip
            ),
            name="SLR_GSIC",
        ),
        GlobalInitConstraint(lambda m: m.slr_cumgsic[0] == 0.015),
        # GIS
        GlobalConstraint(
            lambda m, t: (
                m.slr_cumgis[t] == slr_gis(m.slr_cumgis[t - 1], m.temperature[t - 1], m)
                if t > 0
                else Constraint.Skip
            ),
            name="SLR_GIS",
        ),
        GlobalInitConstraint(lambda m: m.slr_cumgis[0] == 0.006),
        # Total SLR is sum of each contributing factors
        GlobalConstraint(
            lambda m, t: m.total_SLR[t]
            == m.slr_thermal[t] + m.slr_cumgsic[t] + m.slr_cumgis[t],
            name="total_SLR",
        ),
        RegionalConstraint(
            lambda m, t, r: m.damage_costs_non_slr[t, r]
            == m.damage_scale_factor
            * damage_fct(m.temperature[t] - 0.6, m.T0 - 0.6, m, r, is_slr=False),
            "damage_costs_non_slr",
        ),
        RegionalConstraint(
            lambda m, t, r: m.damage_costs_slr[t, r]
            == m.damage_scale_factor
            * damage_fct(m.total_SLR[t], m.total_SLR[0], m, r, is_slr=True),
            "damage_costs_slr",
        ),
        RegionalConstraint(
            lambda m, t, r: m.damage_costs[t, r]
            == m.damage_costs_non_slr[t, r] + m.damage_costs_slr[t, r],
            "damage_costs",
        ),
        GlobalConstraint(
            lambda m, t: m.damage_relative_global[t]
            == (
                sum(m.damage_costs[t, r] * m.GDP_gross[t, r] for r in m.regions)
                / m.global_GDP_gross[t]
            ),
            "damage_relative_global",
        ),
        ####################################
        ####################################
        GlobalConstraint(
            lambda m, t: m.LBD_factor[t]
            == (
                soft_min(
                    (
                        m.cumulative_global_baseline_emissions[t - 1]
                        - m.cumulative_emissions[t - 1]  # Now changed to t-1, check
                    )
                    / m.LBD_scaling
                    + 1.0
                )
                ** m.log_LBD_rate
                if t > 0
                else 1.0
            ),
            name="LBD",
        ),
        GlobalConstraint(
            lambda m, t: m.LOT_factor[t] == 1 / (1 + m.LOT_rate) ** t, "LOT"
        ),
        GlobalConstraint(
            lambda m, t: m.learning_factor[t] == (m.LBD_factor[t] * m.LOT_factor[t]),
            "learning",
        ),
        ####################################
        ####################################
        RegionalInitConstraint(
            lambda m, r: m.relative_abatement[0, r] == 0, "init_carbon_price"
        ),
        RegionalConstraint(
            lambda m, t, r: m.carbonprice[t, r]
            == MAC(m.relative_abatement[t, r], m, t, r),
            "carbonprice",
        ),
        RegionalConstraint(
            lambda m, t, r: (m.mitigation_costs[t, r])
            == AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r]
            + m.import_export_mitigation_cost_balance[t, r],
            "mitigation_costs",
        ),
        RegionalConstraint(
            lambda m, t, r: m.area_under_MAC[t, r]
            == AC(m.relative_abatement[t, r], m, t, r) * m.baseline[t, r],
            "area_under_MAC",
        ),
        RegionalConstraint(
            lambda m, t, r: m.rel_mitigation_costs[t, r]
            == m.mitigation_costs[t, r] / m.GDP_gross[t, r],
            "rel_mitigation_costs",
            doc="$$ \\text{rel_mitigation_costs}_{t,r} = \\frac{\\text{mitigation_costs}_{t,r}}{\\text{GDP_gross}_{t,r}} $$",
        ),
        GlobalConstraint(
            lambda m, t: m.global_rel_mitigation_costs[t]
            == sum(m.mitigation_costs[t, r] for r in m.regions) / m.global_GDP_gross[t],
            "global_rel_mitigation_costs",
        ),
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
                / soft_min(sum(m.regional_emission_reduction[t, r] for r in m.regions))
                if t > 0
                else Constraint.Skip
            ),
            "global_cost_per_emission_reduction_unit",
        ),
        ####################################
        ####################################
        RegionalConstraint(
            lambda m, t, r: m.GDP_net[t, r]
            == m.GDP_gross[t, r]
            * (1 - (m.damage_costs[t, r] if not value(m.ignore_damages) else 0))
            - m.mitigation_costs[t, r]
            - m.financial_transfer[t, r],
            "GDP_net",
        ),
        RegionalConstraint(
            lambda m, t, r: m.investments[t, r] == m.sr * m.GDP_net[t, r],
            "investments",
        ),
        RegionalConstraint(
            lambda m, t, r: m.consumption[t, r] == (1 - m.sr) * m.GDP_net[t, r],
            "consumption",
        ),
        ####################################
        ####################################
        RegionalConstraint(
            lambda m, t, r: m.utility[t, r]
            == calc_utility(m.consumption[t, r], m.population[t, r], m.elasmu),
            "utility",
        ),
        GlobalConstraint(
            lambda m, t: m.yearly_welfare[t]
            == sum(m.population[t, r] * m.utility[t, r] for r in m.regions),
            "yearly_welfare",
        ),
        GlobalInitConstraint(lambda m: m.NPV[0] == 0),
        GlobalConstraint(
            lambda m, t: (
                m.NPV[t]
                == m.NPV[t - 1]
                + m.dt * exp(-m.PRTP * (m.year(t) - m.beginyear)) * m.yearly_welfare[t]
                if t > 0
                else Constraint.Skip
            ),
            name="NPV",
        ),
        ####################################
        ####################################
    ]

    constraints_bounds = [
        GlobalConstraint(
            lambda m, t: (
                m.cumulative_emissions[t]
                - (
                    m.budget
                    + (
                        m.overshoot[t] * (1 - m.perc_reversible_damages)
                        if value(m.perc_reversible_damages) < 1
                        else 0
                    )
                )
                <= 0
                if (m.year(t) >= 2100 and value(m.budget) is not False)
                else Constraint.Skip
            ),
            name="carbon_budget",
        ),
        GlobalConstraint(lambda m, t: m.cumulative_emissions[t] >= 0),
        # Global and regional inertia constraints:
        GlobalConstraint(
            lambda m, t: (
                m.global_emissions[t] - m.global_emissions[t - 1]
                >= m.dt
                * m.inertia_global
                * sum(m.baseline_emissions[0, r] for r in m.regions)
                if value(m.inertia_global) is not False and t > 0
                else Constraint.Skip
            ),
            name="global_inertia",
        ),
        RegionalConstraint(
            lambda m, t, r: (
                m.regional_emissions[t, r] - m.regional_emissions[t - 1, r]
                >= m.dt * m.inertia_regional * m.baseline_emissions[0, r]
                if value(m.inertia_regional) is not False and t > 0
                else Constraint.Skip
            ),
            name="regional_inertia",
        ),
        GlobalConstraint(
            lambda m, t: (
                m.global_emissions[t] >= m.global_min_level
                if value(m.global_min_level) is not False
                else Constraint.Skip
            ),
            "global_min_level",
        ),
        RegionalConstraint(
            lambda m, t, r: (
                m.regional_emissions[t, r] >= m.regional_min_level
                if value(m.regional_min_level) is not False
                else Constraint.Skip
            ),
            "regional_min_level",
        ),
        RegionalConstraint(
            lambda m, t, r: (
                m.regional_emissions[t, r] - m.regional_emissions[t - 1, r] <= 0
                if m.year(t - 1) > 2100 and value(m.non_increasing_emissions_after_2100)
                else Constraint.Skip
            ),
            name="non_increasing_emissions_after_2100",
        ),
        GlobalConstraint(
            lambda m, t: (
                m.global_emissions[t] <= 0
                if (
                    m.year(t) >= 2100
                    and value(m.no_pos_emissions_after_budget_year) is True
                    and value(m.budget) is not False
                )
                else Constraint.Skip
            ),
            name="net_zero_after_2100",
        ),
        RegionalConstraint(
            lambda m, t, r: m.rel_mitigation_costs[t, r]
            >= (m.rel_mitigation_costs_min_level if t > 0 else 0.0),
            "rel_mitigation_costs_non_negative",
        ),
    ]

    return constraints_vars + constraints_bounds
