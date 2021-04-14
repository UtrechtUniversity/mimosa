"""
Utils
"""


from glob import glob
import pandas as pd
from scipy.interpolate import InterpolatedUnivariateSpline


def read_csv(path):
    if "*" in path:
        path = glob(path)[0]
    return pd.read_csv(path)


class InterpolatingData:
    """
    `data` is a dataframe with as row-indices the regions (or "Global"), and as
    columns the years used in the ConcreteModel
    """

    def __init__(self, data):
        self.maxyear = float(data.columns[-1])
        self.region_interp_fct = {
            region: InterpolatedUnivariateSpline(row.index.astype(float), row.values)
            for region, row in data.iterrows()
        }

    def get(self, region, year):
        value = self.region_interp_fct[region](year)
        if len(value.shape) == 0:
            return float(value)
        return value
