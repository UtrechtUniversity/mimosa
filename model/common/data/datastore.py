"""
Create a DataStore object which reads and parses regional data
from a data file in IIASA database format
"""

import os
from typing import Callable, Dict
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

from model.common import economics
from .utils import UnitValues, extrapolate


class DataStore:
    """The DataStore object is used when instantiating a concrete model from the
    abstract model. It provides values for time and region dependent data:
      - baseline emissions
      - population
      - baseline GDP / carbon intensity
      - TFP
    This data is read from a data file in IIASA format, and automatically transformed
    to the right units as specified in the config file.

    Usage: once the data store is initialised, only the method `DataStore.data_object` will
    be used.
    """

    # Class property and not instance property to reduce redundancy
    databases = {}
    cached_data = {}

    def __init__(self, params, quant, regional_param_store):
        self.params = params
        self.quant = quant  # Quantity object for unit conversion
        self._select_database()
        self._create_data_years()

        baseline = self._create_data_values("emissions", "emissionsrate_unit")
        population = self._create_data_values("population", "population_unit")
        gdp = self._create_data_values("GDP", "currency_unit")
        self._data_values = {
            "baseline": baseline,
            "population": population,
            "GDP": gdp,
            "carbon_intensity": {
                r: UnitValues(baseline[r].xvalues, baseline[r].yvalues / gdp[r].yvalues)
                for r in params["regions"]
            },
            "TFP": {
                r: economics.get_TFP(
                    r, self.data_years, gdp, population, regional_param_store
                )
                for r in params["regions"]
            },
        }

    def _select_database(self):
        """Makes sure the file doesn't need to be read multiple times"""
        filename = os.path.join(
            os.path.dirname(__file__), "../../../", self.params["input"]["db_filename"],
        )
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

    def _create_data_values(self, variable, to_unit=None) -> Dict[str, UnitValues]:
        regions = self.params["regions"]
        return {
            region: self._get_data(self.data_years, region, variable, to_unit)
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

    def _get_data(self, output_years, region, variable, to_unit=None) -> UnitValues:

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
        return UnitValues(output_years, interp_fct(output_years), unit)

    def _interp_data(self, year, region, variable):
        values = self._data_values[variable][region]
        return np.interp(year, values.xvalues, values.yvalues)

    def data_object(self, variable: str) -> Callable[[int, str], float]:
        """Creates a function giving the value of `variable` at a given year and regions.

        Args:
            variable (str): any of the keys of self._data_values

        Returns:
            Callable[[int, str], float]: interpolating function of type f(year, region)
        """
        return lambda year, region: self._interp_data(year, region, variable)

    def __repr__(self):
        return "DataStore with data values {} calculated on the years {}-{} from input file {} for the regions {} and {}".format(
            list(self._data_values.keys()),
            self.data_years[0],
            self.data_years[-1],
            self.filename,
            list(self.params["regions"].keys()),
            self.params["SSP"],
        )
