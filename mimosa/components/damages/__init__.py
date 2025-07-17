"""
Imports the different damage modules
"""

from . import coacch, nodamage, accreu

DAMAGE_MODULES = {
    "COACCH": coacch.get_constraints,
    "ACCREU": accreu.get_constraints,
    "nodamage": nodamage.get_constraints,
}
