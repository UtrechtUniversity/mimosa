"""
Imports the different damage cost trading modules
"""

from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import notransfer, globaldamagepool


FINANCIALTRANSFER_MODULES = {
    "notransfer": notransfer.get_constraints,
    "globaldamagepool": globaldamagepool.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Build the selected financialtransfer module."""

    module = inputs.config_value("model structure.financialtransfer module")
    get_module_constraints = load_from_registry(module, FINANCIALTRANSFER_MODULES)
    return get_module_constraints(m, inputs)
