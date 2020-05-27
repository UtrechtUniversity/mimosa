from pint import UnitRegistry
from model.common.config import params

ureg = UnitRegistry()
ureg.load_definitions('input/units.txt')
Q = ureg.Quantity

def parse_default_units(units):
    for key, value in params['default units'].items():
        units = units.replace(key, value)
    return units

def custom_replace(units):
    return units.replace('US$', 'USD')

def to_default_units(values, unit, target_units):
    # First parse target units with default units
    target_units = parse_default_units(custom_replace(target_units))
    unit = custom_replace(unit)
    with_unit = Q(values, unit).to(target_units)
    return with_unit