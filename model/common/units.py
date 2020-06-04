from pint import UnitRegistry
from model.common.config import params

ureg = UnitRegistry()
ureg.load_definitions('input/units.txt')

def parse_default_units(units):
    for key, value in params['default units'].items():
        # Add brackets () to avoid order of operation problems with compound units
        units = units.replace(key, f'({value})')
    return units

def custom_replace(units):
    return units.replace('US$', 'USD')

def Quant(*args, only_magnitude=True):
    """Usage:
    - Quant(string, to_unit):        Quant('20 GtCO2/yr', 'emissionsrate_unit')
    - Quant(value, unit, to_unit):   Quant(20, 'GtCO2/yr', 'emissionsrate_unit')
    """
    
    if len(args) not in [2, 3]: # If number of arguments is not 2 or 3
        raise RuntimeError("Incorrect number of arguments to Q")
    
    if (args[0] is False): # Sometimes a quantity (like carbon budget) can be skipped by setting to False
        return False
    
    # First parse target units with default units
    target_unit = parse_default_units(custom_replace(args[-1]))

    if len(args) == 2:
        string = custom_replace(str(args[0]))
        quantity = ureg.Quantity(string)
    elif len(args) == 3:
        value = args[0]
        unit = custom_replace(str(args[1]))
        quantity = ureg.Quantity(value, unit)

    if only_magnitude:
        return quantity.to(target_unit).magnitude
    else:
        return quantity.to(target_unit)
   