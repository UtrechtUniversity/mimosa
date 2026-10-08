"""
Imports the different damage modules
"""

from mimosa.common import ConcreteModel
from mimosa.common.utils import load_from_registry
from mimosa.core.model_inputs import ModelInputs

from . import coacch, nodamage, accreu


DAMAGE_MODULES = {
    "COACCH": coacch.get_constraints,
    "ACCREU": accreu.get_constraints,
    "ACCREU_CGE": accreu.cge_damages.get_constraints,
    "nodamage": nodamage.get_constraints,
}


def get_constraints(m: ConcreteModel, inputs: ModelInputs):
    """Build the selected damage module."""

    module = inputs.config_value("model structure.damage module")
    get_module_constraints = load_from_registry(module, DAMAGE_MODULES)
    return get_module_constraints(m, inputs)
