"""
Imports the different welfare modules
"""

from . import welfare_loss_minimising
from . import cost_minimising
from . import inequal_aversion_general

WELFARE_MODULES = {
    "welfare_loss_minimising": welfare_loss_minimising.get_constraints,
    "cost_minimising": cost_minimising.get_constraints,
    "inequal_aversion_general": inequal_aversion_general.get_constraints,
}
