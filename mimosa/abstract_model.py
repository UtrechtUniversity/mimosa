"""
Abstract representation of the model
--------------------------------------------
Contains all model equations and constraints
"""

from mimosa.common import Param, AbstractModel, Set, add_constraint, quant, Equation
from mimosa.common.utils import load_from_registry
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
    get_damage_constraints = load_from_registry(damage_module, damages.DAMAGE_MODULES)
    constraints.extend(get_damage_constraints(m))

    # Abatement costs
    constraints.extend(mitigation.get_constraints(m))

    # Emission trading
    get_emissiontrade_constraints = load_from_registry(
        emissiontrade_module, emissiontrade.EMISSIONTRADE_MODULES
    )
    constraints.extend(get_emissiontrade_constraints(m))

    # Financial transfer
    get_financialtransfer_constraints = load_from_registry(
        financialtransfer_module, financialtransfer.FINANCIALTRANSFER_MODULES
    )
    constraints.extend(get_financialtransfer_constraints(m))

    # Effort sharing regime
    get_effortsharing_constraints = load_from_registry(
        effortsharing_regime, effortsharing.EFFORTSHARING_MODULES
    )
    constraints.extend(get_effortsharing_constraints(m))

    # Cobb-Douglas and economics
    constraints.extend(cobbdouglas.get_constraints(m))

    # Utility and welfare
    get_welfare_constraints = load_from_registry(
        welfare_module, welfare.WELFARE_MODULES
    )
    constraints.extend(get_welfare_constraints(m))

    # Objective of optimisation
    get_objective_constraints = load_from_registry(
        objective_module, objective.OBJECTIVE_MODULES
    )
    model_objective, objective_constraints = get_objective_constraints(m)
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

    m.objective = model_objective

    return m, equations
