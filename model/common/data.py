"""
Create a DataStore object which reads and parses regional data
from a data file in IIASA database format
"""

from typing import Iterable
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from model.common import economics, dataclass


class DataStore:

    # Class property and not instance property to reduce redundancy
    databases = {}
    cached_data = {}

    def __init__(self, params, quant, regional_param_store):
        self.params = params
        self.quant = quant  # Quantity object for unit conversion
        self._select_database()
        self._create_data_years()
        self.data_values = {
            "baseline": self._create_data_values("emissions", "emissionsrate_unit"),
            "population": self._create_data_values("population", "population_unit"),
            "GDP": self._create_data_values("GDP", "currency_unit"),
        }
        self.data_values["carbon_intensity"] = {
            r: self.data_values["baseline"][r] / self.data_values["GDP"][r]
            for r in params["regions"]
        }
        self.data_values["TFP"] = {
            r: economics.get_TFP(r, self, regional_param_store)
            for r in params["regions"]
        }

    def _select_database(self):
        """Makes sure the file doesn't need to be read multiple times"""
        filename = self.params["input"]["db_filename"]
        if filename not in DataStore.databases:
            database = pd.read_csv(filename)
            database.columns = database.columns.str.lower()
            DataStore.databases[filename] = database
            self.cached_data[filename] = {}

        self.database = DataStore.databases[filename]
        self.cache = self.cached_data[filename]
        self.filename = filename

    def _create_data_years(self):
        beginyear = self.params["time"]["start"]
        endyear = self.params["time"]["end"] + 50  # Make sure extrapolation goes well
        dt = self.params["time"]["dt"]
        self.data_years = np.arange(beginyear, endyear, dt)

    def _create_data_values(self, variable, to_unit=None):
        regions = self.params["regions"]
        return {
            region: self.get_data(self.data_years, region, variable, to_unit).values
            for region in regions
        }

    def _get_data_from_database(self, region, variable):

        SSP = self.params["SSP"]
        model = self.params["input"]["baselines"][SSP]["model"]
        scenario = self.params["input"]["baselines"][SSP]["scenario"]
        variablename = self.params["input"]["variables"][variable]

        cached_data = self._get_cached_data_from_database(
            model, scenario, region, variablename
        )

        return cached_data["years"], cached_data["values"], cached_data["unit"]

    def _get_cached_data_from_database(self, model, scenario, region, variablename):
        key = (model, scenario, region, variablename)
        if key not in self.cache:
            database = self.database
            selection = database.loc[
                (database["model"] == model)
                & (database["scenario"] == scenario)
                & (database["region"] == (region[:-1] if region[-1] == "#" else region))
                & (database["variable"] == variablename)
            ]

            if len(selection) != 1:
                raise Exception(
                    "Found {} rows matching criteria ({}, {}, {}, {}) instead of one.".format(
                        len(selection), model, scenario, region, variablename
                    )
                )

            self.cache[key] = {
                "years": selection.loc[:, "2010":].columns.values.astype(float),
                "values": selection.loc[:, "2010":].values[0],
                "unit": selection.iloc[0]["unit"],
            }
        return self.cache[key]

    def get_data(self, year, region, variable, to_unit=None):

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
        interp_fct = interp1d(extended_years, extended_data, kind="cubic")
        return ValueUnit(interp_fct(year), unit)

    def interp_data(self, year, region, variable):
        return np.interp(year, self.data_years, self.data_values[variable][region])

    def data_object(self, variable):
        return lambda year, region: self.interp_data(year, region, variable)

    def __repr__(self):
        return "DataStore with data values {} calculated on the years {}-{} from input file {} for the regions {} and {}".format(
            list(self.data_values.keys()),
            self.data_years[0],
            self.data_years[-1],
            self.filename,
            list(self.params["regions"].keys()),
            self.params["SSP"],
        )


###########################
##
## Utils
##
###########################


@dataclass
class ValueUnit:
    values: Iterable
    unit: str


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
        change = minmax(
            0.0, change_rate - change_rate * (t_prev - 2100.0) / stabilising_years
        )
        val = val_prev + change * (t - t_prev)
        # if val < 0:
        #     val = 0.1
        #     became_negative = True

        new_values.append(val)

        val_prev = val
        t_prev = t

    if became_negative:
        print("Extrapolation became negative for", meta_info)
    return np.concatenate([input_values, new_values])
