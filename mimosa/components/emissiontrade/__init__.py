"""
Imports the different emission trading modules
"""

from . import globalcostpool, notrade, emissiontrade

EMISSIONTRADE_MODULES = {
    "notrade": notrade.get_constraints,
    "globalcostpool": globalcostpool.get_constraints,
    "emissiontrade": emissiontrade.get_constraints,
}
