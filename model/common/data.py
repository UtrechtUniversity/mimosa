import numpy as np
import pandas as pd

from model.common.config import params
from model.common import units

### Load SSP database
database = pd.read_csv(params['input']['db_filename'])

# Get data from database
def get_data_from_database(region, SSP, variable):
    
    model = params['input']['baselines'][SSP]['model']
    scenario = params['input']['baselines'][SSP]['scenario']
    variablename = params['input']['variables'][variable]
    
    selection = database.loc[
        (database['MODEL'] == model)
        & (database['SCENARIO'] == scenario)
        & (database['REGION'] == (region[:-1] if region[-1] == '#' else region))
        & (database['VARIABLE'] == variablename)
    ]
    
    if len(selection) != 1:
        raise Exception(
            "Found {} rows matching criteria ({}, {}, {}, {}) instead of one.".format(
                len(selection), model, scenario, region, variablename
            )
        )
    
    years = selection.loc[:,'2010':].columns.values.astype(float)
    values = selection.loc[:,'2010':].values[0]
    unit = selection.iloc[0]['UNIT']
    
    return years, values, unit





# To extrapolate: take growth rate 2090-2100, linearly bring it down to growth rate of 0 in 2150
def extrapolate(input, years, extra_years, stabilising_years=50):
    # First get final change rate
    change_rate = (input[-1] - input[-2]) / (years[-1] - years[-2])
    minmax = np.maximum if change_rate > 0 else np.minimum

    t_prev = years[-1]
    val_prev = input[-1]

    new_values = []

    for t in extra_years:
        change = minmax(0.0, change_rate - change_rate * (t_prev - 2100.0) / stabilising_years)
        val = val_prev + change * (t-t_prev)

        new_values.append(val)

        val_prev = val
        t_prev = t

    return np.concatenate([input, new_values])



def get_data(year, region, SSP, variable, to_unit=None):
    # 1. Get data from database
    years, values, unit = get_data_from_database(region, SSP, variable)
    if to_unit is not None:
        quantity = units.to_default_units(values, unit, to_unit)
        values = quantity.magnitude
        unit = quantity.units


    # 2. Extrapolate this data to beyond 2100
    extra_years = np.arange(2110, 2260, 10)
    extended_data = extrapolate(values, years, extra_years)
    extended_years = np.concatenate([years, extra_years])

    # 3. Interpolate the combined data
    return {
        'values': np.interp(year, extended_years, extended_data),
        'unit': unit
    }


