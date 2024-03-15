"""
Abstract representation of the model
--------------------------------------------
Contains all model equations and constraints
"""

import numpy as np
from mimosa.common import Param, AbstractModel, Set, add_constraint
from mimosa.components import (
    effortsharing,
    emissions,
    emissiontrade,
    financialtransfer,
    cobbdouglas,
    damages,
    mitigation,
    objective,
    sealevelrise,
    welfare,
)


######################
# Create model
######################


def create_abstract_model(
    damage_module: str,
    emissiontrade_module: str,
    financialtransfer_module: str,
    welfare_module: str,
    objective_module: str,
) -> AbstractModel:
    """
    ## Building the abstract model

    Builds the abstract model for MIMOSA by combining all components. Some components are optional. In the
    parameters, different variants of some components can be chosen. The components are:

    - `damage_module`: The damage module to use
    - `emissiontrade_module`: The emission trading module to use
    - `financialtransfer_module`: The financial transfer module to use
    - `welfare_module`: The welfare module to use
    - `objective_module`: The objective module to use

    """
    m = AbstractModel()

    ## Constraints
    # Each constraint will be put in this list,
    # then added to the model at the end of this file.
    constraints = []

    ## Time and region
    m.beginyear = Param()
    m.dt = Param()
    m.tf = Param()
    m.t = Set()
    m.year = None  # Initialised with concrete instance
    m.year2100 = Param()

    m.regions = Set(ordered=True)

    ######################
    # Create data functions
    # Will be initialised when creating a concrete instance of the model
    ######################

    m.baseline_emissions = lambda year, region: None
    m.population = lambda year, region: None
    m.TFP = lambda year, region: None
    m.GDP = lambda year, region: None
    m.carbon_intensity = lambda year, region: None

    def baseline_cumulative(year_start, year_end, region):
        years = np.linspace(year_start, year_end, 100)
        return np.trapz(m.baseline_emissions(years, region), x=years)

    m.baseline_cumulative = baseline_cumulative
    m.baseline_cumulative_global = lambda m, year_start, year_end: sum(
        baseline_cumulative(year_start, year_end, r) for r in m.regions
    )

    ######################
    # Components
    ######################

    # Emissions and temperature equations
    constraints.extend(emissions.get_constraints(m))

    # Sea level rise
    constraints.extend(sealevelrise.get_constraints(m))

    # Damage costs
    if damage_module == "RICE2010":
        constraints.extend(damages.ad_rice2010.get_constraints(m))
    elif damage_module == "WITCH":
        constraints.extend(damages.ad_witch.get_constraints(m))
    elif damage_module == "RICE2012":
        constraints.extend(damages.ad_rice2012.get_constraints(m))
    elif damage_module == "COACCH":
        constraints.extend(damages.coacch.get_constraints(m))
    elif damage_module == "nodamage":
        constraints.extend(damages.nodamage.get_constraints(m))
    else:
        raise NotImplementedError

    # Abatement costs
    constraints.extend(mitigation.get_constraints(m))

    # Emission trading
    if emissiontrade_module == "notrade":
        constraints.extend(emissiontrade.notrade.get_constraints(m))
    elif emissiontrade_module == "globalcostpool":
        constraints.extend(emissiontrade.globalcostpool.get_constraints(m))
    elif emissiontrade_module == "emissiontrade":
        constraints.extend(emissiontrade.emissiontrade.get_constraints(m))
    else:
        raise NotImplementedError(
            f"Emission trading module `{emissiontrade_module}` not implemented"
        )

    # Financial transfer
    if financialtransfer_module == "notransfer":
        constraints.extend(financialtransfer.notransfer.get_constraints(m))
    elif financialtransfer_module == "globaldamagepool":
        constraints.extend(financialtransfer.globaldamagepool.get_constraints(m))
    else:
        raise NotImplementedError(
            f"Financial transfer module `{financialtransfer_module}` not implemented"
        )

    # Effort sharing regime
    constraints.extend(effortsharing.get_constraints(m))

    # Cobb-Douglas and economics
    constraints.extend(cobbdouglas.get_constraints(m))

    # Utility and welfare
    if welfare_module == "welfare_loss_minimising":
        constraints.extend(welfare.welfare_loss_minimising.get_constraints(m))
    elif welfare_module == "cost_minimising":
        constraints.extend(welfare.cost_minimising.get_constraints(m))
    elif welfare_module == "inequal_aversion_general":
        constraints.extend(welfare.inequal_aversion_general.get_constraints(m))
    else:
        raise NotImplementedError(f"Welfare module `{welfare_module}` not implemented")

    # Objective of optimisation
    if objective_module == "utility":
        objective_rule, objective_constraints = objective.utility.get_constraints(m)
    elif objective_module == "globalcosts":
        objective_rule, objective_constraints = objective.globalcosts.get_constraints(m)
    else:
        raise NotImplementedError

    constraints.extend(objective_constraints)

    ######################
    # Add constraints to abstract model
    ######################

    for constraint in constraints:
        add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)

    m.obj = objective_rule

    return m
