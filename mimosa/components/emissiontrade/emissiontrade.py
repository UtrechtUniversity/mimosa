"""
Model equations and constraints:
Emission trading module
Type: trading of emissions, and not costs
"""

from typing import Sequence

from mimosa.common import (
    AbstractModel,
    GeneralConstraint,
    GlobalConstraint,
    RegionalConstraint,
    Var,
    NonNegativeReals,
    quant,
    sqrt,
)

from mimosa.components.abatement import AC


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """Emission trading equations and constraints
    (trading of emissions specification)

    Necessary variables:
        m.abatement_costs (abatement costs as paid for by this region)

    Returns:
        list of constraints (any of:
           - GlobalConstraint
           - GlobalInitConstraint
           - RegionalConstraint
           - RegionalInitConstraint
        )
    """
    constraints = []

    # Default options for variables defined below
    opts_emiss = {"units": quant.unit("emissions_unit"), "within": NonNegativeReals}
    opts_costs = {"units": quant.unit("currency_unit"), "within": NonNegativeReals}

    # Emission reduction in region r paid for by region r
    m.own_emission_reduction = Var(m.t, m.regions, **opts_emiss)
    m.own_emission_reduction_costs = Var(m.t, m.regions, **opts_costs)

    # Emission reduction in other regions paid for by region r
    m.imported_emission_reduction = Var(m.t, m.regions, **opts_emiss)
    m.imported_emission_reduction_costs = Var(m.t, m.regions, **opts_costs)

    # Emission reduction in region r paid for by other regions
    m.exported_emission_reduction = Var(m.t, m.regions, initialize=0.01, **opts_emiss)
    m.exported_emission_reduction_costs = Var(m.t, m.regions, **opts_costs)

    # Actual emission reduction (will be equal to own + exported reductions)
    m.actual_emission_reduction = Var(m.t, m.regions, **opts_emiss)

    # Totals of imported and exported emissions
    m.total_exported_reductions = Var(m.t, **opts_emiss)
    m.total_exported_reduction_costs = Var(m.t, **opts_costs)

    constraints.extend(
        [
            GlobalConstraint(
                lambda m, t: m.total_exported_reductions[t]
                == sum(m.exported_emission_reduction[t, r] for r in m.regions),
                "total_exported_emissions",
            ),
            GlobalConstraint(
                lambda m, t: m.total_exported_reduction_costs[t]
                == sum(m.exported_emission_reduction_costs[t, r] for r in m.regions),
                "total_exported_reduction_costs",
            ),
            GlobalConstraint(
                lambda m, t: m.total_exported_reductions[t]
                == sum(m.imported_emission_reduction[t, r] for r in m.regions),
                "total_imported_equals_total_exported_emission_reductions",
            ),
        ]
    )

    constraints.extend(
        [
            # Costs for imported emission reductions: imported reductions have a global price
            RegionalConstraint(
                lambda m, t, r: m.imported_emission_reduction_costs[t, r]
                == m.imported_emission_reduction[t, r]
                * m.total_exported_reduction_costs[t]
                / m.total_exported_reductions[t],
                "costs_for_imported_emission_reductions",
            ),
            # Costs of the own emission reductions: the "cheap" part of the MAC
            RegionalConstraint(
                lambda m, t, r: m.own_emission_reduction_costs[t, r]
                == AC(m.own_emission_reduction[t, r] / m.baseline[t, r], m, t, r)
                * m.baseline[t, r],
                "costs_own_emission_reductions",
            ),
            # Costs of exported emission reductions: calculated as the "expensive" part of the MAC
            # This is the area under the MAC for the total emission reduction (own + exported) minus
            # the costs of the own reductions.
            RegionalConstraint(
                lambda m, t, r: m.actual_emission_reduction[t, r]
                == m.own_emission_reduction[t, r] + m.exported_emission_reduction[t, r],
                "actual_emission_reduction",
            ),
            RegionalConstraint(
                lambda m, t, r: m.exported_emission_reduction_costs[t, r]
                == AC(
                    m.actual_emission_reduction[t, r] / m.baseline[t, r],
                    m,
                    t,
                    r,
                )
                * m.baseline[t, r]
                - m.own_emission_reduction_costs[t, r],
                "costs_exported_emission_reductions",
            ),
            # Actual reductions and actual abatement costs:
            RegionalConstraint(
                lambda m, t, r: m.relative_abatement[t, r]
                == m.actual_emission_reduction[t, r] / m.baseline[t, r],
                "relative_abatement",
            ),
            RegionalConstraint(
                lambda m, t, r: m.abatement_costs[t, r]
                == m.own_emission_reduction_costs[t, r]
                + 1.02 * m.imported_emission_reduction_costs[t, r],
                "abatement_costs",
            ),
        ]
    )

    return constraints
