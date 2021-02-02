import numpy as np
from numpy.lib.function_base import interp
import pandas as pd

from model.common import economics, utils
import input.regional_data
from scipy.interpolate import interp1d

# To extrapolate: take growth rate 2090-2100, linearly bring it down to growth rate of 0 in 2150
# Not sure if this should rather be a method of DataStore
def extrapolate(input_values, years, extra_years, meta_info, stabilising_years=50):

    became_negative = False

    # First get final change rate
    change_rate = (input_values[-1] - input_values[-2]) / (years[-1] - years[-2])
    minmax = np.maximum if change_rate > 0 else np.minimum

    t_prev = years[-1]
    val_prev = input_values[-1]

    new_values = []

    for t in extra_years:
        change = minmax(0.0, change_rate - change_rate * (t_prev - 2100.0) / stabilising_years)
        val = val_prev + change * (t-t_prev)
        # if val < 0:
        #     val = 0.1
        #     became_negative = True

        new_values.append(val)

        val_prev = val
        t_prev = t

    if became_negative:
        print("Extrapolation became negative for", meta_info)
    return np.concatenate([input_values, new_values])



class DataStore:

    # Class property and not instance property to reduce redundancy
    databases = {}
    cached_data = {}

    def __init__(self, params, quant):
        self.params = params
        self.quant = quant          # Quantity object for unit conversion
        self._select_database()
        self._create_data_years()
        self.data_values = {
            'baseline': self._create_data_values('emissions', 'emissionsrate_unit'),
            'population': self._create_data_values('population', 'population_unit'),
            'GDP': self._create_data_values('GDP', 'currency_unit')
        }
        self.data_values['carbon_intensity'] = {
            r: self.data_values['baseline'][r] / self.data_values['GDP'][r]
            for r in params['regions']
        }
        self.data_values['TFP'] = {r: economics.get_TFP(r, self) for r in params['regions']}


    def _select_database(self):
        """Makes sure the file doesn't need to be read multiple times"""
        filename = self.params['input']['db_filename']
        if filename not in self.databases:
            df = pd.read_csv(filename)
            df.columns= df.columns.str.lower()
            self.databases[filename] = df
            self.cached_data[filename] = {}
            
        self.database = self.databases[filename]
        self.cache = self.cached_data[filename]
        self.filename = filename
    
    
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
    

    def _get_data_from_database(self, region, variable):
        
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
                (database['model'] == model)
                & (database['scenario'] == scenario)
                & (database['region'] == (region[:-1] if region[-1] == '#' else region))
                & (database['variable'] == variablename)
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
                'unit': selection.iloc[0]['unit']
            }
        return self.cache[key]
    
    def get_data(self, year, region, variable, to_unit=None):
        # TMP:
        if region == 'WorldOrig':
            years, values, unit = original_replication_data(variable, self.params['SSP'])
        else:
            # 1. Get data from database
            years, values, unit = self._get_data_from_database(region, variable)
        if to_unit is not None:
            quantity = self.quant(values, unit, to_unit, only_magnitude=False)
            values = quantity.magnitude
            unit = quantity.units


        # 2. Extrapolate this data to beyond 2100
        extra_years = np.arange(2110, 2260, 10)
        extended_data = extrapolate(values, years, extra_years, [variable, region])
        extended_years = np.concatenate([years, extra_years])

        # 3. Interpolate the combined data
        interp_fct = interp1d(extended_years, extended_data, kind='cubic')
        # desample = np.array([2020, 2100, 2250]) # remove all info between 2020 and 2100
        # interp_fct = interp1d(desample, interp_fct(desample), kind='quadratic') 
        return {
            'values': interp_fct(year),
            # 'values': np.interp(year, extended_years, extended_data),
            'unit': unit
        }
    
    def interp_data(self, year, region, variable):
        return np.interp(year, self.data_years, self.data_values[variable][region])

    def data_object(self, variable):
        return lambda year, region: self.interp_data(year, region, variable)

    def get_regional(self, *params):
        return {r: self._get_regional_param(params, r) for r in self.params['regions']}

    def _get_regional_param(self, params, r):
        # Loop down the tree of parameters, checking for @regional
        curr_param = self.params['regions'][r]
        for param in params:
            curr_param = curr_param[param]
            if curr_param == '$regional':
                return input.regional_data.get_param_value(r, params, self.params)
        return curr_param
    

    def __repr__(self):
        return 'DataStore with data values {} calculated on the years {}-{} from input file {} for the regions {} and {}'.format(
            list(self.data_values.keys()),
            self.data_years[0], self.data_years[-1],
            self.filename,
            list(self.params['regions'].keys()),
            self.params['SSP']
        )
    




def original_replication_data(variable, SSP):
    years = np.arange(2010, 2100+1, 10)
    baseline_emissions_data = {
        'SSP1': 1e-3 * np.array([35488.81804,40069.00391,42653.23405,43778.4961,42454.75782,41601.92839,39217.53158,33392.29395,28618.4139,24612.91358]),
        'SSP2': 1e-3 * np.array([35612.61459,43478.01205,49474.44434,52913.73829,55991.09929,57621.59506,60866.66667,64443.06316,67837.07162,72492.60678]),
        'SSP3': 1e-3 * np.array([35710.44369,46649.57129,53669.32943,56344.23796,61127.10743,61307.10352,63838.6862,66926.7142,70980.4362,76477.13477]),
        'SSP4': 1e-3 * np.array([35594.47461,42463.96029,48287.80144,50825.20638,50388.90886,48402.19857,47702.92872,47037.72234,44735.16667,44358.89291]),
        'SSP5': 1e-3 * np.array([35982.45736,46630.57553,60289.7181,72707.2142,86440.4922,94748.90105,105555.3053,110432.9245,112423.4447,111910.0397])
    }
    population_data = {
        'SSP1': 1e-3 * np.array([6921.797852, 7576.10498, 8061.937988, 8388.762695, 8530.5, 8492.175781, 8298.950195, 7967.387207, 7510.454102, 6957.98877]),
        'SSP2': 1e-3 * np.array([6921.797852, 7671.501953, 8327.682617, 8857.175781, 9242.542969, 9459.967773, 9531.094727, 9480.227539, 9325.707031, 9103.234375]),
        'SSP3': 1e-3 * np.array([6921.797852, 7746.918945, 8571.573242, 9324.817383, 10038.44043, 10671.42969, 11232.58008, 11768.17969, 12288.11035, 12793.15039]),
        'SSP4': 1e-3 * np.array([6921.797852, 7660.201172, 8300.902344, 8818.331055, 9212.981445, 9459.842773, 9573.267578, 9592.255859, 9542.825195, 9456.296875]),
        'SSP5': 1e-3 * np.array([6921.797852, 7584.920898, 8091.687988, 8446.890625, 8629.456055, 8646.706055, 8520.380859, 8267.616211, 7901.399902, 7447.205078])
    }
    GDP_data = {
        'SSP1': 1e-3 * np.array([68461.88281, 101815.2969, 155854.7969, 223195.5, 291301.4063, 356291.4063, 419291.1875, 475419.1875, 524875.8125, 565389.625]),
        'SSP2': 1e-3 * np.array([68461.88281, 101602.2031, 144812.9063, 188496.5938, 234213.4063, 283250.5938, 338902.5, 399688.5938, 466015.8125, 538245.875]),
        'SSP3': 1e-3 * np.array([68461.88281, 100879.5, 135704.5938, 160926.5, 180601, 197332.2031, 215508.2969, 234786.4063, 255673.7969, 279511.1875]),
        'SSP4': 1e-3 * np.array([68461.88281, 103664.2969, 147928.2969, 191229.5, 229272.7969, 262242.4063, 292255.1875, 317266.6875, 339481.8125, 360479.5]),
        'SSP5': 1e-3 * np.array([68461.88281, 105689.8984, 174702.2969, 271955.0938, 378443.0938, 492278.5938, 617695.3125, 749892.8125, 889666.3125, 1034177.])
    }

    if variable == 'emissions': 
        return years, baseline_emissions_data[SSP], 'Gt CO2/yr'
    if variable == 'population': 
        return years, population_data[SSP], 'billion'
    if variable == 'GDP': 
        return years, GDP_data[SSP], 'trillion USD2005/yr'

    raise Exception('Unknown variable {}'.format(variable))
