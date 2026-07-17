"""Component catalogue and construction of MIMOSA's abstract model."""

from typing import List, Tuple

from mimosa.common import (
    AbstractModel,
    add_constraint,
    Equation,
    ModelContext,
)
from mimosa.base_model import create_base_model
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
from mimosa.core.component_definition import (
    fixed_component,
    selectable_component,
    validate_unique_component_names,
)

#######################
# Component catalogue
#######################

# The tuple order is the order in which model components are constructed.
# The name of each component corresponds to the name in the parameters file.
MODEL_COMPONENTS = (
    # Emissions and temperature
    fixed_component("emissions", emissions.get_constraints),
    # Sea-level rise
    fixed_component("sealevelrise", sealevelrise.get_constraints),
    # Damage costs
    selectable_component("damage", damages.DAMAGE_MODULES),
    # Mitigation costs
    fixed_component("mitigation", mitigation.get_constraints),
    # Emission trading and financial transfers
    selectable_component("emissiontrade", emissiontrade.EMISSIONTRADE_MODULES),
    selectable_component(
        "financialtransfer", financialtransfer.FINANCIALTRANSFER_MODULES
    ),
    # Effort-sharing regime
    selectable_component("effortsharing", effortsharing.EFFORTSHARING_MODULES),
    # Production and consumption
    fixed_component("cobbdouglas", cobbdouglas.get_constraints),
    # Utility and welfare
    selectable_component("welfare", welfare.WELFARE_MODULES),
)

# The objective has a different return value and is therefore built separately.
OBJECTIVE_COMPONENT = selectable_component("objective", objective.OBJECTIVE_MODULES)

ALL_COMPONENTS = MODEL_COMPONENTS + (OBJECTIVE_COMPONENT,)
validate_unique_component_names(ALL_COMPONENTS)


########################
# Build abstract model
########################


def create_abstract_model(
    context: ModelContext,
) -> Tuple[AbstractModel, List[Equation]]:
    """
    ## Building the abstract model

    Builds the abstract model for MIMOSA by combining all components. Some components are optional. In the
    parameters, different variants of some components can be chosen. The components are:

    - [`damage module`](../parameters.md#model structure.damage module): The damage module to use
    - [`emissiontrade module`](../parameters.md#model structure.emissiontrade module): The emission trading module to use
    - [`financialtransfer module`](../parameters.md#model structure.financialtransfer module): The financial transfer module to use
    - [`welfare module`](../parameters.md#model structure.welfare module): The welfare module to use
    - [`objective module`](../parameters.md#model structure.objective module): The objective module to use
    - [`effortsharing module`](../parameters.md#model structure.effortsharing module): The effort-sharing module to use

    """
    m = create_base_model()

    # Each constraint will be put in this list,
    # then added to the model at the end of this file.
    constraints = []

    # Add all ordinary model components in catalogue order.
    for component in MODEL_COMPONENTS:
        constraints.extend(component.build(m, context))

    # Objective of optimisation
    model_objective, objective_constraints = OBJECTIVE_COMPONENT.build(m, context)
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
