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


def sum_over_regions(m, var, t):
    """Helper function to sum over regions for a given variable."""
    try:
        return var[t, :].sum()
    except (AttributeError, TypeError):
        return sum(var[t, r] for r in m.regions)


class Multiply:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __getitem__(self, key):
        return self.a[key] * self.b[key]


expressions_rhs = {
    "capital_stock": lambda m, t, r: (
        m.capital_stock[t - 1, r]
        + m.dt
        * economics.calc_dKdt(
            m.capital_stock[t - 1, r], m.dk, m.investments[t - 1, r], m.dt
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
    "global_GDP_gross": lambda m, t: (sum_over_regions(m, m.GDP_gross, t)),
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
        sum_over_regions(m, m.regional_emissions, t)
        if t > 0
        else sum_over_regions(m, m.regional_emissions, 0)
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
        sum_over_regions(m, Multiply(m.damage_costs, m.GDP_gross), t)
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
        sum_over_regions(m, m.mitigation_costs, t)
        / soft_min(sum_over_regions(m, m.regional_emission_reduction, t))
        if t > 0
        else 0
    ),
    "global_emission_reduction_per_cost_unit": lambda m, t: (
        sum_over_regions(m, m.regional_emission_reduction, t)
        / soft_min(sum_over_regions(m, m.mitigation_costs, t))
        if t > 0
        else 0
    ),
    "global_rel_mitigation_costs": lambda m, t: (
        sum_over_regions(m, m.mitigation_costs, t) / m.global_GDP_gross[t]
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
        sum_over_regions(m, Multiply(m.population, m.utility), t)
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

    return constraints + constraints_bounds
