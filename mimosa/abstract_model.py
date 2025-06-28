"""
Abstract representation of the model
--------------------------------------------
Contains all model equations and constraints
"""

from mimosa.common import Param, AbstractModel, Set, add_constraint, quant, Equation
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
    effortsharing_regime: str,
) -> AbstractModel:
    """
    ## Building the abstract model

    Builds the abstract model for MIMOSA by combining all components. Some components are optional. In the
    parameters, different variants of some components can be chosen. The components are:

    - [`damage_module`](../parameters.md#model.damage%20module): The damage module to use
    - [`emissiontrade_module`](../parameters.md#model.emissiontrade%20module): The emission trading module to use
    - [`financialtransfer_module`](../parameters.md#model.financialtransfer%20module): The financial transfer module to use
    - [`welfare_module`](../parameters.md#model.welfare%20module): The welfare module to use
    - [`objective_module`](../parameters.md#model.objective%20module): The objective module to use
    - [`effortsharing_regime`](../parameters.md#effort%20sharing.regime): The effort sharing regime to use

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
    # Create data params for baseline values
    ######################

    m.population = Param(
        m.t,
        m.regions,
        doc="timeandregional::population",
        units=quant.unit("billion people"),
    )
    m.global_population = Param(
        m.t,
        initialize=lambda m, t: sum(m.population[t, r] for r in m.regions),
        units=quant.unit("billion people"),
    )
    m.baseline_GDP = Param(
        m.t,
        m.regions,
        doc="timeandregional::GDP",
        units=quant.unit("currency_unit"),
    )
    m.baseline_emissions = Param(
        m.t,
        m.regions,
        doc="timeandregional::emissions",
        units=quant.unit("emissionsrate_unit"),
    )
    m.MAC_SSP_calibration_factor = Param(m.t, units=quant.unit("dimensionless"))

    ######################
    # Components
    ######################

    # Emissions and temperature equations
    constraints.extend(emissions.get_constraints(m))

    # Sea level rise
    constraints.extend(sealevelrise.get_constraints(m))

    # Damage costs
    if damage_module == "COACCH":
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
    if effortsharing_regime == "noregime":
        constraints.extend(effortsharing.noregime.get_constraints(m))
    elif effortsharing_regime == "equal_mitigation_costs":
        constraints.extend(effortsharing.equal_mitigation_costs.get_constraints(m))
    elif effortsharing_regime == "equal_total_costs":
        constraints.extend(effortsharing.equal_total_costs.get_constraints(m))
    elif effortsharing_regime == "per_cap_convergence":
        constraints.extend(effortsharing.per_cap_convergence.get_constraints(m))
    elif effortsharing_regime == "ability_to_pay":
        constraints.extend(effortsharing.ability_to_pay.get_constraints(m))
    elif effortsharing_regime == "equal_cumulative_per_cap":
        constraints.extend(effortsharing.equal_cumulative_per_cap.get_constraints(m))
    else:
        raise NotImplementedError(
            f"Effort sharing regime `{effortsharing_regime}` not implemented"
        )

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

    ######################
    # Get all equations (not constraints) for simulation mode
    ######################
    equations = [eq for eq in constraints if isinstance(eq, Equation)]

    m.obj = objective_rule

    return m, equations
