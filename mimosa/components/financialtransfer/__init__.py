"""
Imports the different damage cost trading modules
"""

from . import notransfer, globaldamagepool

FINANCIALTRANSFER_MODULES = {
    "notransfer": notransfer.get_constraints,
    "globaldamagepool": globaldamagepool.get_constraints,
}
