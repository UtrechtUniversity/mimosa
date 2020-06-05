import numpy as np
import pandas as pd

from model.common import economics
from model.common.config import params
from model.common.units import Quant

# To extrapolate: take growth rate 2090-2100, linearly bring it down to growth rate of 0 in 2150
# Not sure if this should rather be a method of DataStore
def extrapolate(input_values, years, extra_years, stabilising_years=50):
    # First get final change rate
    change_rate = (input_values[-1] - input_values[-2]) / (years[-1] - years[-2])
    minmax = np.maximum if change_rate > 0 else np.minimum

    t_prev = years[-1]
    val_prev = input_values[-1]

    new_values = []

    for t in extra_years:
        change = minmax(0.0, change_rate - change_rate * (t_prev - 2100.0) / stabilising_years)
        val = val_prev + change * (t-t_prev)

        new_values.append(val)

        val_prev = val
        t_prev = t

    return np.concatenate([input_values, new_values])



class DataStore:

    # Class property and not instance property to reduce redundancy
    databases = {}
    cached_data ={}

    def __init__(self, params):
        self.params = params
        self._select_database()
        self._create_data_years()
        self.data_values = {
            'baseline': self._create_data_values('emissions', 'emissionsrate_unit'),
            'population': self._create_data_values('population', 'population_unit'),
            'GDP': self._create_data_values('GDP', 'currency_unit')
        }
        self.data_values['TFP'] = {r: economics.get_TFP(r, self) for r in params['regions']}


    def _select_database(self):
        """Makes sure the file doesn't need to be read multiple times"""
        filename = self.params['input']['db_filename']
        if filename not in self.databases:
            self.databases[filename] = pd.read_csv(filename)
            self.cached_data[filename] = {}
            
        self.database = self.databases[filename]
        self.cache = self.cached_data[filename]
    
    
    def _create_data_years(self):
        beginyear = self.params['time']['start']
        endyear = self.params['time']['end'] + 50 # Make sure extrapolation goes well
        dt = self.params['time']['dt']
        self.data_years = np.arange(beginyear, endyear, dt)
        
    
    def _create_data_values(self, variable, to_unit=None):
        regions = self.params['regions']
        return {
            region: self.get_data(self.data_years, region, variable, to_unit)['values']
            for region in regions
        }
    

    def get_data_from_database(self, region, variable):
        
        database = self.database
    
        SSP = self.params['SSP']
        model = self.params['input']['baselines'][SSP]['model']
        scenario = self.params['input']['baselines'][SSP]['scenario']
        variablename = self.params['input']['variables'][variable]
        
        cached_data = self._get_cached_data_from_database(model, scenario, region, variablename)
    
        return cached_data['years'], cached_data['values'], cached_data['unit']
    
    def _get_cached_data_from_database(self, model, scenario, region, variablename):
        key = (model, scenario, region, variablename)
        if key not in self.cache:
            database = self.database
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

            self.cache[key] = {
                'years': selection.loc[:,'2010':].columns.values.astype(float),
                'values': selection.loc[:,'2010':].values[0],
                'unit': selection.iloc[0]['UNIT']
            }
        return self.cache[key]
    
    def get_data(self, year, region, variable, to_unit=None):
        # 1. Get data from database
        years, values, unit = self.get_data_from_database(region, variable)
        if to_unit is not None:
            quantity = Quant(values, unit, to_unit, only_magnitude=False)
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
    
    def interp_data(self, t, region, variable):
        year = self.params['time']['start'] + t
        return np.interp(year, self.data_years, self.data_values[variable][region])
    
    


