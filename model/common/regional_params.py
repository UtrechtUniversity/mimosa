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


class RegionalParamStore:
    """
    Used to read and parse regional parameter values from various input files
    """

    def __init__(self, params):
        self.params = params

    def get(self, region, name):
        pass


# Make one object for Main, for RICE2010, for RICE2012 since they each have
# their own regional aggregation


class RegionalParameters:
    def __init__(self):
        test = RegionalParamStore(1)

