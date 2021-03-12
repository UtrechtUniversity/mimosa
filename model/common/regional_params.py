"""
Create a RegionalParamStore object which reads and parses regional
parameter values from various input files

These regional values are:
  [Main]
  - MAC scaling factor
  - Initial capital factor

  [RICE2010]
  - a1, a2, a3
  - g1, g2

  [RICE2012]
  - a1, a2, a3
  - nu1, nu2, nu3,
  - SLRDAM1, SLRDAM2

"""

import os
import pandas as pd


class RegionalParamStore:
    """
    Used to read and parse regional parameter values from various input files
    """

    def __init__(self, params):
        self.params = params
        self.regions = params["regions"]

        self.categories = {
            "init_capital_factor": RegionalParameters("init_capital_factor.csv"),
            "mac": RegionalParameters("mac.csv"),
        }

    def get(self, category, paramname):
        return {
            region: self.getregional(category, paramname, region)
            for region in self.regions
        }

    def getregional(self, category, paramname, region):
        # First check if parameter is set manually in config file
        try:
            return self.params["regions"][region][category][paramname]
        except (KeyError, TypeError):
            pass

        return self.categories[category].get(paramname, region)


# Make one object for Main, for RICE2010, for RICE2012 since they each have
# their own regional aggregation


class RegionalParameters:
    def __init__(self, filename):
        full_filename = os.path.join(
            os.path.dirname(__file__), "../../inputdata/params", filename,
        )
        self.data = pd.read_csv(full_filename).set_index("region")

    def get(self, paramname, region):
        return self.data.loc[region, paramname]
