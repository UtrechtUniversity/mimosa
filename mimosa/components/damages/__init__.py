"""
Imports the different damage modules
"""

from . import coacch, nodamage

DAMAGE_MODULES = {
    "COACCH": coacch.get_constraints,
    "nodamage": nodamage.get_constraints,
}
