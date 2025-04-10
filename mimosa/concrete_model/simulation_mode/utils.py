"""
Utils
"""

from glob import glob

import numpy as np
from mimosa.common.data.utils import extrapolate
import pandas as pd
from scipy.interpolate import InterpolatedUnivariateSpline
from mimosa.common import logger


def read_csv(path):
    if "*" in path:
        paths = glob(path)
        if len(paths) != 1:
            logger.warning(
                "Warning: matched {} files instead of 1 for file pattern {}".format(
                    len(paths), path
                )
            )
        path = glob(path)[0]
    return pd.read_csv(path)


class InterpolatingData:
    """
    `data` is a dataframe with as row-indices the regions (or "Global"), and as
    columns the years used in the ConcreteModel
    """

    def __init__(self, data):
        # extrapolate
        self.minyear = float(data.columns[0])
        self.maxyear = float(data.columns[-1])
        self.region_interp_fct = {
            region: self.interp(row) for region, row in data.iterrows()
        }

    @staticmethod
    def interp(row):
        values = row.values
        years = row.index.astype(float).to_numpy()
        extra_years = np.arange(years[-1] + 5, 2151, 5)

        new_values = extrapolate(values, years, extra_years, "for_simulation_mode")
        all_years = np.concatenate([years, extra_years])
        return InterpolatedUnivariateSpline(all_years, new_values)

    def get(self, region, year):
        if year < self.minyear or year > self.maxyear:
            return None
        try:
            value = self.region_interp_fct[region](year)
            if len(value.shape) == 0:
                return float(value)
            return value
        except KeyError:
            return None
