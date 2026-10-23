"""
Imports the different welfare modules
"""

from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import welfare_loss_minimising
from . import cost_minimising
from . import inequal_aversion_general


WELFARE_MODULES = {
    "welfare_loss_minimising": welfare_loss_minimising.get_constraints,
    "cost_minimising": cost_minimising.get_constraints,
    "inequal_aversion_general": inequal_aversion_general.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Build the selected welfare module."""

    module = inputs.config_value("model structure.welfare module")
    get_module_constraints = load_from_registry(module, WELFARE_MODULES)
    return get_module_constraints(m, inputs)
