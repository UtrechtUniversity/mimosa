"""
Uses the Pint package to parse quantities with units.
The custom units are loaded from a text file.
"""
import os
from pyomo.environ import units as pyomo_units

from .utils import load_yaml


pyomo_units.load_definitions_from_file(
    os.path.join(os.path.dirname(__file__), "../inputdata/config", "extra_units.txt")
)

DEFAULT_UNITS = load_yaml("default_units.yaml")


class Quantity:
    """
    The Quantity object creates a callable object which parses quantities
    with units (see __call__ usage).

    Args:
        params (dict): contains all Param values

    """

    def __init__(self):
        self.default_units = DEFAULT_UNITS
        self._pint_registry = pyomo_units.pint_registry
        self._pyomo_units_container = pyomo_units

    def __call__(self, *args, only_magnitude=True, can_be_false=True):
        """Usage:
        - Quant(string, to_unit):        Quant('20 GtCO2/yr', 'emissionsrate_unit')
        - Quant(value, unit, to_unit):   Quant(20, 'GtCO2/yr', 'emissionsrate_unit')
        """

        if len(args) not in [2, 3]:  # If number of arguments is not 2 or 3
            raise RuntimeError("Incorrect number of arguments to Q")

        if args[0] is False and can_be_false:
            # Sometimes a quantity (like carbon budget) can be skipped by setting to False
            return False

        # First parse target units with default units
        target_unit = self._parse_default_units(self._custom_replace(args[-1]))

        if len(args) == 2:
            string = self._custom_replace(str(args[0]))
            quantity = self._pint_registry.Quantity(string)
        elif len(args) == 3:
            value = args[0]
            unit = self._custom_replace(str(args[1]))
            quantity = self._pint_registry.Quantity(value, unit)
        else:
            raise Exception("Wrong usage of Quant function")

        if only_magnitude:
            return quantity.to(target_unit).magnitude
        return quantity.to(target_unit)

    def __repr__(self):
        units = ", ".join(
            [f"{key}: {value}" for key, value in self.default_units.items()]
        )
        return f"Quantity with units: {units}"

    def unit(self, unit_str: str, pyomo=True):
        """Returns a Pyomo unit object given a string with units.

        If pyomo=false, returns a Pint unit object.

        First it replaces custom default units:
            - currency_unit
            - emissionsrate_unit
            - emissions_unit
            - temperature_unit
            - population_unit
        to the respective default unit as defined in default_units.yaml
        (which is also stored in this object as `self.default_units`)
        """

        default_units_replaced = self._parse_default_units(unit_str)
        if pyomo:
            return getattr(self._pyomo_units_container, default_units_replaced)

        return self._pint_registry.Unit(default_units_replaced)

    ####### Private functions #######

    def _parse_default_units(self, units):
        for key, value in self.default_units.items():
            # Add brackets () to avoid order of operation problems with compound units
            units = units.replace(key, f"({value})")
        # Bugfix for a Pint bug where aliases are treated wrongly
        units = units.replace("year", "yr")
        return units

    @staticmethod
    def _custom_replace(units):
        return units.replace("US$", "USD").replace("t CO2", "tCO2")


quant = Quantity()
