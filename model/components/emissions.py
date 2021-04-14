"""
Model equations and constraints:
Emissions and temperature
"""

from typing import Sequence
from model.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    GlobalConstraint,
    GlobalInitConstraint,
    RegionalConstraint,
    RegionalInitConstraint,
    Constraint,
    value,
)


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emissions and temperature equations and constraints

    Necessary variables:
        m.relative_abatement
        m.cumulative_emissions
        m.T0
        m.temperature

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    m.regional_emissions = Var(m.t, m.regions)
    m.baseline = Var(m.t, m.regions)
    m.baseline_carbon_intensity = Param()

    m.relative_abatement = Var(m.t, m.regions, initialize=0, bounds=(0, 2))
    m.cumulative_emissions = Var(m.t)
    m.global_emissions = Var(m.t)

    constraints.extend(
        [
            # Baseline emissions based on emissions or carbon intensity
            RegionalConstraint(
                lambda m, t, r: (
                    m.baseline[t, r]
                    == m.carbon_intensity(m.year(t), r) * m.GDP_net[t, r]
                )
                if value(m.baseline_carbon_intensity)
                else (m.baseline[t, r] == m.baseline_emissions(m.year(t), r)),
                name="baseline_emissions",
            ),
            # Regional emissions from baseline and relative abatement
            RegionalConstraint(
                lambda m, t, r: m.regional_emissions[t, r]
                == (1 - m.relative_abatement[t, r])
                * m.baseline_emissions(m.year(t), r),
                "regional_abatement",
            ),
            RegionalInitConstraint(
                lambda m, r: m.regional_emissions[0, r]
                == m.baseline_emissions(m.year(0), r)
            ),
            # Global emissions (sum from regional emissions)
            GlobalConstraint(
                lambda m, t: m.global_emissions[t]
                == sum(m.regional_emissions[t, r] for r in m.regions),
                "global_emissions",
            ),
            GlobalInitConstraint(
                lambda m: m.global_emissions[0]
                == sum(m.baseline_emissions(m.year(0), r) for r in m.regions),
                "global_emissions_init",
            ),
            # Cumulative global emissions
            GlobalConstraint(
                lambda m, t: m.cumulative_emissions[t]
                == m.cumulative_emissions[t - 1] + m.dt * m.global_emissions[t]
                if t > 0
                else Constraint.Skip,
                "cumulative_emissions",
            ),
            GlobalInitConstraint(lambda m: m.cumulative_emissions[0] == 0),
        ]
    )

    m.T0 = Param()
    m.temperature = Var(m.t, initialize=lambda m, t: m.T0)
    m.TCRE = Param()
    m.temperature_target = Param()
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.temperature[t]
                == m.T0 + m.TCRE * m.cumulative_emissions[t],
                "temperature",
            ),
            GlobalInitConstraint(lambda m: m.temperature[0] == m.T0),
            GlobalConstraint(
                lambda m, t: m.temperature[t] <= m.temperature_target
                if (m.year(t) >= 2100 and value(m.temperature_target) is not False)
                else Constraint.Skip,
                name="temperature_target",
            ),
        ]
    )

    m.perc_reversible_damages = Param()

    # m.overshoot = Var(m.t, initialize=0)
    # m.overshootdot = DerivativeVar(m.overshoot, wrt=m.t)
    # m.netnegative_emissions = Var(m.t)
    # global_constraints.extend(
    #     [
    #         lambda m, t: m.netnegative_emissions[t]
    #         == m.global_emissions[t] * (1 - tanh(m.global_emissions[t] * 10)) / 2
    #         if value(m.perc_reversible_damages) < 1
    #         else Constraint.Skip,
    #         lambda m, t: m.overshootdot[t]
    #         == (m.netnegative_emissions[t] if t <= value(m.year2100) and t > 0 else 0)
    #         if value(m.perc_reversible_damages) < 1
    #         else Constraint.Skip,
    #     ]
    # )

    # global_constraints_init.extend([lambda m: m.overshoot[0] == 0])

    # Emission constraints

    m.budget = Param()
    m.inertia_global = Param()
    m.inertia_regional = Param()
    m.global_min_level = Param()
    m.regional_min_level = Param()
    m.no_pos_emissions_after_budget_year = Param()
    constraints.extend(
        [
            # Carbon budget constraints:
            GlobalConstraint(
                lambda m, t: m.cumulative_emissions[t]
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
                else Constraint.Skip,
                name="carbon_budget",
            ),
            GlobalConstraint(
                lambda m, t: m.global_emissions[t] <= 0
                if (
                    m.year(t) >= 2100
                    and value(m.no_pos_emissions_after_budget_year) is True
                    and value(m.budget) is not False
                )
                else Constraint.Skip,
                name="net_zero_after_2100",
            ),
            GlobalConstraint(lambda m, t: m.cumulative_emissions[t] >= 0),
            # Global and regional inertia constraints:
            GlobalConstraint(
                lambda m, t: m.global_emissions[t] - m.global_emissions[t - 1]
                >= m.dt
                * m.inertia_global
                * sum(m.baseline_emissions(m.year(0), r) for r in m.regions)
                if value(m.inertia_global) is not False and t > 0
                else Constraint.Skip,
                name="global_inertia",
            ),
            RegionalConstraint(
                lambda m, t, r: m.regional_emissions[t, r]
                - m.regional_emissions[t - 1, r]
                >= m.dt * m.inertia_regional * m.baseline_emissions(m.year(0), r)
                if value(m.inertia_regional) is not False and t > 0
                else Constraint.Skip,
                name="regional_inertia",
            ),
            GlobalConstraint(
                lambda m, t: m.global_emissions[t] >= m.global_min_level
                if value(m.global_min_level) is not False
                else Constraint.Skip,
                "global_min_level",
            ),
            RegionalConstraint(
                lambda m, t, r: m.regional_emissions[t, r] >= m.regional_min_level
                if value(m.regional_min_level) is not False
                else Constraint.Skip,
                "regional_min_level",
            ),
        ]
    )

    m.emission_relative_cumulative = Var(m.t, initialize=1)
    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: (
                    m.emission_relative_cumulative[t]
                    == m.cumulative_emissions[t]
                    / m.baseline_cumulative_global(m, m.year(0), m.year(t))
                )
                if t > 0
                else Constraint.Skip,
                name="relative_cumulative_emissions",
            ),
            GlobalInitConstraint(lambda m: m.emission_relative_cumulative[0] == 1),
        ]
    )

    return constraints
