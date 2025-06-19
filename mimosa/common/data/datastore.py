"""
Create a DataStore object which reads and parses regional data
from a data file in IIASA database format
"""

import os
from typing import Dict
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from mimosa.common import quant
from .utils import UnitValues, extrapolate


class DataStore:
    """The DataStore object is used when instantiating a concrete model from the
    abstract mimosa. It provides values for time and region dependent data:

    This data is read from a data file in IIASA format, and automatically transformed
    to the right units as specified in the config file.
    """

    # Class property and not instance property to reduce redundancy
    databases = {}
    cached_data = {}

    def __init__(self, params):
        self.params = params

        self._create_data_years()
        self._data_values = {}

        for var_name, var_info in params["input"]["variables"].items():
            self._select_database(var_info["file"])
            self._data_values[var_name] = self._create_data_values(var_info)

    def _select_database(self, filename):
        """Makes sure the file doesn't need to be read multiple times"""
        full_path = os.path.join(
            os.path.dirname(__file__),
            "../../",
            filename,
        )
        if filename not in DataStore.databases:
            database = pd.read_csv(full_path)
            database.columns = database.columns.str.lower()
            DataStore.databases[filename] = database
            self.cached_data[filename] = {}

    def _create_data_years(self):
        beginyear = self.params["time"]["start"]
        endyear = self.params["time"]["end"] + 50  # Make sure extrapolation goes well
        dt = self.params["time"]["dt"]
        self.data_years = np.arange(beginyear, endyear, dt)

    def _create_data_values(self, var_info) -> Dict[str, UnitValues]:
        regions = self.params["regions"]
        return {
            region: self._get_data(self.data_years, region, var_info)
            for region in regions
        }

    def _get_cached_data_from_database(self, var_info, region):
        filename = var_info["file"]
        model = var_info["model"]
        scenario = var_info["scenario"]
        variablename = var_info["variable"]
        key = (model, scenario, region, variablename)
        if key not in self.cached_data[filename]:
            database = DataStore.databases[filename]
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

            self.cached_data[filename][key] = {
                "years": selection.loc[:, "2010":].columns.values.astype(float),
                "values": selection.loc[:, "2010":].values[0],
                "unit": selection.iloc[0]["unit"],
            }
        return self.cached_data[filename][key]

    def _get_data(self, output_years, region, var_info) -> UnitValues:
        # 1. Get data from database
        years_values_unit = self._get_cached_data_from_database(var_info, region)
        years = years_values_unit["years"]
        values = years_values_unit["values"]
        unit = years_values_unit["unit"]

        if "unit" in var_info:
            quantity = quant(values, unit, var_info["unit"], only_magnitude=False)
            values = quantity.magnitude
            unit = quantity.units

        # 2. Extrapolate this data to beyond 2100
        extra_years = np.arange(2110, 2260, 10)
        extended_data = extrapolate(
            values, years, extra_years, [var_info["variable"], region]
        )
        extended_years = np.concatenate([years, extra_years])

        # 3. Interpolate the combined data
        interp_fct = interp1d(extended_years, extended_data, kind="cubic")
        return UnitValues(output_years, interp_fct(output_years), unit)

    def interp_data(self, year, region, variable):
        values = self._data_values[variable][region]
        return np.interp(year, values.xvalues, values.yvalues)

    def interp_data_from_dict(self, year, keyframes: dict):
        return np.interp(year, list(keyframes.keys()), list(keyframes.values()))

    def __repr__(self):
        return "DataStore with data values {} calculated on the years {}-{} for the regions {} and {}".format(
            list(self._data_values.keys()),
            self.data_years[0],
            self.data_years[-1],
            list(self.params["regions"].keys()),
            self.params["SSP"],
        )
