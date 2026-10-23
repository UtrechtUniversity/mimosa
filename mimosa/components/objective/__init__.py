"""
Imports the different objective modules
"""

from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import globalcosts
from . import utility


OBJECTIVE_MODULES = {
    "utility": utility.get_constraints,
    "globalcosts": globalcosts.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Build the selected objective module."""

    module = inputs.config_value("model structure.objective module")
    get_module_constraints = load_from_registry(module, OBJECTIVE_MODULES)
    return get_module_constraints(m, inputs)
