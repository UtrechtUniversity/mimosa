import numpy as np

from model.common import data, utils, units
from model.common.config import params
from model.common.units import Quant
from model.common import economics, emissions


##############################################
# Creates the GEKKO variables and parameters
# --------------------------------------------
# Creates the objects, gives them their
# initial value and lower/upper bounds
#
# Exogenous:
#  - Parameter: m.Param
#
# Endogenous:
#  - State variable: m.SV
#  - Control variable: m.CV
#
# Regional: m.Array({m.SV,m.CV,m.Param})
#
##############################################



###### Exogenous variables (parameters)

def create_baseline_array(m, regions, years):
    """Get emission data from input for baseline emissions

    Returns:
        baseline_emissions -- Array for every region
        baseline_cumulative -- Array for every region
    """

    baseline_emissions = m.Array(m.Param, len(regions))
    baseline_cumulative = m.Array(m.Param, len(regions))

    for i, region in enumerate(regions):
        baseline_data = data.get_data(years, region, params['SSP'], 'emissions', 'emissionsrate_unit')
        baseline_emissions[i].value = baseline_data['values']
        baseline_cumulative[i].value = [
            np.trapz(baseline_data['values'][:i+1], years[:i+1])
            for i in range(len(years))
        ]

    unit = baseline_data['unit']
    return baseline_emissions, baseline_cumulative


def create_population_array(m, regions, years):
    population_array = m.Array(m.Param, len(regions))
    for i, region in enumerate(regions):
        population_data = data.get_data(years, region, params['SSP'], 'population', 'population_unit')
        population_array[i].value = population_data['values']

    unit = population_data['unit']
    return population_array


def create_TFP_array(m, regions, years):
    TFP_array = m.Array(m.Param, len(regions))
    for i, region in enumerate(regions):
        TFP_array[i].value = economics.get_TFP(years, region)

    return TFP_array




###### Endogenous variables (parameters)

def create_temperature(m, final_baseline_cumulative):
    T0 = Quant(params['temperature']['initial'], 'temperature_unit')
    TCRE = Quant(params['temperature']['TCRE'], '(temperature_unit)/(emissions_unit)')
    temperature = m.SV(T0, lb=T0, ub=T0+TCRE*final_baseline_cumulative)
    return temperature


def create_cumulative_emissions(m, final_baseline_cumulative):
    cumulative_emissions = m.SV(value=0, lb=0, ub=final_baseline_cumulative, name='CE')
    return cumulative_emissions


def create_global_emissions(m, regions, baseline_emissions):
    global_emissions = m.SV(
        value=utils.total_at_t(baseline_emissions),
        lb=-emissions.max_emissions(baseline_emissions),
        ub=emissions.max_emissions(baseline_emissions)
    )
    return global_emissions


def create_NPV(m):
    NPV = m.SV(value=0, lb=0, name='NPV')
    return NPV


def create_relative_abatement(m, regions):
    relative_abatement = m.Array(
        m.CV, len(regions),
        value=0, lb=0, ub=params['GEKKO']['upperbounds']['relative_abatement']
    )
    return relative_abatement


def create_capital_stock(m, regions, years):
    upper_bound_rel_to_GDP = 3.0
    capital_stock = m.Array(m.SV, len(regions))
    for i, region in enumerate(regions):
        GDP_baseline = data.get_data(years, region, params['SSP'], 'GDP', 'currency_unit')['values']
        capital_stock[i].value = Quant(regions[region]['initial capital'], 'currency_unit')
        capital_stock[i].lower = GDP_baseline[0] * 0.5
        capital_stock[i].upper = GDP_baseline[-1] * upper_bound_rel_to_GDP
    return capital_stock


def create_regional_emissions(m, regions, baseline_emissions):
    regional_emissions = m.Array(m.SV, len(regions))
    for i, region in enumerate(regions):
        regional_emissions[i].value = baseline_emissions[i].value[0]
    return regional_emissions



    