"""Construction of MIMOSA's concrete model."""

from typing import List, Tuple

from mimosa.common import (
    ConcreteModel,
    add_constraint,
    Equation,
)
from mimosa.base_model import create_base_model
from mimosa.core.model_inputs import ModelInputs
from mimosa.components import (
    cobbdouglas,
    damages,
    effortsharing,
    emissions,
    emissiontrade,
    financialtransfer,
    mitigation,
    objective,
    sealevelrise,
    welfare,
)


########################
# Build concrete model
########################


def create_model(
    inputs: ModelInputs,
) -> Tuple[ConcreteModel, List[Equation]]:
    """
    ## Building the concrete model

    Builds the concrete model for MIMOSA by combining all components. Some components are optional. In the
    parameters, different variants of some components can be chosen. The components are:

    - [`damage module`](../parameters.md#model structure.damage module): The damage module to use
    - [`emissiontrade module`](../parameters.md#model structure.emissiontrade module): The emission trading module to use
    - [`financialtransfer module`](../parameters.md#model structure.financialtransfer module): The financial transfer module to use
    - [`welfare module`](../parameters.md#model structure.welfare module): The welfare module to use
    - [`objective module`](../parameters.md#model structure.objective module): The objective module to use
    - [`effortsharing module`](../parameters.md#model structure.effortsharing module): The effort-sharing module to use

    """
    m = create_base_model(inputs)

    # Each constraint will be put in this list,
    # then added to the model at the end of this file.
    constraints = []

    # Emissions, temperature and sea-level rise
    constraints.extend(emissions.get_constraints(m, inputs))
    constraints.extend(sealevelrise.get_constraints(m, inputs))

    # Damage and mitigation costs
    constraints.extend(damages.get_constraints(m, inputs))
    constraints.extend(mitigation.get_constraints(m, inputs))

    # Emission trading, financial transfers and effort sharing
    constraints.extend(emissiontrade.get_constraints(m, inputs))
    constraints.extend(financialtransfer.get_constraints(m, inputs))
    constraints.extend(effortsharing.get_constraints(m, inputs))

    # Production, consumption and welfare
    constraints.extend(cobbdouglas.get_constraints(m, inputs))
    constraints.extend(welfare.get_constraints(m, inputs))

    # Objective of optimisation
    model_objective, objective_constraints = objective.get_constraints(m, inputs)
    constraints.extend(objective_constraints)

    ######################
    # Add constraints to concrete model
    ######################

    for constraint in constraints:
        add_constraint(m, constraint.to_pyomo_constraint(m), constraint.name)

    ######################
    # Get all equations (not constraints) for simulation mode
    ######################
    equations = [eq for eq in constraints if isinstance(eq, Equation)]

    m.objective = model_objective

    return m, equations
