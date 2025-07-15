"""
Imports the different objective modules
"""

from . import globalcosts
from . import utility

OBJECTIVE_MODULES = {
    "utility": utility.get_constraints,
    "globalcosts": globalcosts.get_constraints,
}
