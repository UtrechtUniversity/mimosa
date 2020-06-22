##############################################
# Model equations and constraints:
# Emissions and temperature
#
##############################################

from pyomo.environ import *
from pyomo.dae import *

def constraints(m):
    """Emissions and temperature equations and constraints

    Necessary variables:
        m.relative_abatement
        m.cumulative_emissions
        m.T0
        m.temperature

    Returns:
        dict: {
            global:         global_constraints,
            global_init:    global_constraints_init,
            regional:       regional_constraints,
            regional_init:  regional_constraints_init
        }
    """
    global_constraints      = []
    global_constraints_init = []
    regional_constraints    = []
    regional_constraints_init = []

    m.regional_emissions = Var(m.t, m.regions)
    m.relative_abatement = Var(m.t, m.regions, initialize=0, bounds=(0, 2))
    m.cumulative_emissions = Var(m.t)
    m.global_emissions = Var(m.t)

    m.regional_emissionsdot     = DerivativeVar(m.regional_emissions, wrt=m.t)
    m.cumulative_emissionsdot   = DerivativeVar(m.cumulative_emissions, wrt=m.t)
    m.global_emissionsdot       = DerivativeVar(m.global_emissions, wrt=m.t)

    regional_constraints.append(lambda m,t,r: m.regional_emissions[t, r] == (1-m.relative_abatement[t, r]) * m.baseline(t, r))
    global_constraints.append(lambda m,t: m.global_emissions[t] == sum(m.regional_emissions[t, r] for r in m.regions))
    global_constraints.append(lambda m,t: m.cumulative_emissionsdot[t] == m.global_emissions[t])

    m.T0            = Param()
    m.temperature   = Var(m.t, initialize=lambda m,t: m.T0)
    m.temperaturedot = DerivativeVar(m.temperature, wrt=m.t)
    m.TCRE          = Param()
    global_constraints.append(lambda m,t: m.temperature[t] == m.T0 + m.TCRE * m.cumulative_emissions[t])

    # Emission constraints

    m.budget        = Param()
    m.inertia_global = Param()
    m.inertia_regional = Param()
    m.min_level     = Param()
    m.no_pos_emissions_after_budget_year = Param()
    global_constraints.extend([
        lambda m,t: m.cumulative_emissions[t] - m.budget <= 0   if (t >= value(m.year2100) and value(m.budget) is not False) else Constraint.Skip,
        lambda m,t: m.cumulative_emissions[t] >= 0,
        lambda m,t: m.global_emissionsdot[t] >= m.inertia_global * sum(m.baseline(0, r) for r in m.regions) \
                                                                if value(m.inertia_global) is not False else Constraint.Skip,
        lambda m,t: m.global_emissions[t] >= m.min_level        if value(m.min_level) is not False else Constraint.Skip,
        lambda m,t: m.global_emissions[t] <= 0                  if (
                t >= value(m.year2100) and
                value(m.no_pos_emissions_after_budget_year) is True and
                value(m.budget) is not False
            ) else Constraint.Skip
    ])
    regional_constraints.append(
        lambda m,t,r: m.regional_emissionsdot[t, r] >= m.inertia_regional * m.baseline(0, r) \
                                                                if value(m.inertia_regional) is not False else Constraint.Skip
    )


    m.emission_relative_cumulative = Var(m.t)
    global_constraints.append(
        lambda m,t: (
            m.emission_relative_cumulative[t] == m.cumulative_emissions[t] / sum(m.baseline_cumulative(t, r) for r in m.regions)
         ) if t > 0 else Constraint.Skip
    )

    global_constraints_init.extend([
        lambda m: m.temperature[0] == m.T0,
        lambda m: m.global_emissions[0] == sum(m.baseline(0,r) for r in m.regions),
        lambda m: m.cumulative_emissions[0] == 0,
        lambda m: m.emission_relative_cumulative[0] == 1
    ])
    regional_constraints_init.extend([
        lambda m,r: m.regional_emissions[0,r] == m.baseline(0,r),
        lambda m,r: m.carbonprice[0,r] == 0
    ])

    return {
        'global':       global_constraints,
        'global_init':  global_constraints_init,
        'regional':     regional_constraints,
        'regional_init': regional_constraints_init
    }