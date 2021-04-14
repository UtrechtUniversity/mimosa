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

from .regional_param_container import RegionalParamContainer


###########################
#
# Define the store
#
###########################


class RegionalParamStore:
    """
    Used to read and parse regional parameter values from various input files.

    The data is read from different CSV files: one CSV file per "category". 
    Each category is an object of type `RegionalParameters` and contains
    the data for one or multiple parameters:
        - economics: `init_capital_factor`
        - MAC: `kappa`
        - ADRICE2010: all the regional AD-RICE2010 parameters (`a1`, `a2`, `a3`, `g1`, `g2`)
        - ADRICE2012: all the regional AD-RICE2012 parameters
                        (`a1`, `a2`, `a3`, `nu1`, `nu2`, `nu3`, `slrdam1`, `slrdam2`)
    
    Each of these categories has an associated region type, saying which regions are present.
    Conversion between region types happens within the `RegionalParameters` object.

    To get the parameter values for a parameter name, the function `get` is used (or,
    `getregional` if only a single region is needed)
    """

    def __init__(self, params):
        self.params = params
        self.regions = params["regions"]

        regiontype_output = params["regionstype"]

        self.categories = {
            "economics": RegionalParamContainer(
                "economics.csv", "IMAGE26", regiontype_output
            ),
            "MAC": RegionalParamContainer("mac.csv", "IMAGE26", regiontype_output),
            "ADRICE2010": RegionalParamContainer(
                "ADRICE2010.csv", "ADRICE2010", regiontype_output
            ),
            "ADRICE2012": RegionalParamContainer(
                "ADRICE2012.csv", "ADRICE2012", regiontype_output
            ),
            "COACCH": RegionalParamContainer("COACCH.csv", "COACCH", regiontype_output),
        }

    def get(self, category, paramname):
        return {
            region: self.getregional(category, paramname, region)
            for region in self.regions
        }

    def getregional(self, category, paramname, region):
        # First check if parameter is set manually in config file
        try:
            value = self.params["regions"][region][category][paramname]
        except (KeyError, TypeError):
            value = self.categories[category].get(paramname, region)

        return value
