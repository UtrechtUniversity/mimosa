"""
Imports the different emission trading modules
"""

from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import globalcostpool, notrade, emissiontrade


EMISSIONTRADE_MODULES = {
    "notrade": notrade.get_constraints,
    "globalcostpool": globalcostpool.get_constraints,
    "emissiontrade": emissiontrade.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Build the selected emissiontrade module."""

    module = inputs.config_value("model structure.emissiontrade module")
    get_module_constraints = load_from_registry(module, EMISSIONTRADE_MODULES)
    return get_module_constraints(m, inputs)
