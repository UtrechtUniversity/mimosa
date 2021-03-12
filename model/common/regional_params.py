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
import typing
import pandas as pd


###########################
#
# Define the store
#
###########################


class RegionalParamStore:
    """
    Used to read and parse regional parameter values from various input files
    """

    def __init__(self, params):
        self.params = params
        self.regions = params["regions"]

        regiontype_output = params["regionstype"]

        self.categories = {
            "economics": RegionalParameters(
                "economics.csv", "IMAGE26", regiontype_output
            ),
            "MAC": RegionalParameters("mac.csv", "IMAGE26", regiontype_output),
            "ADRICE2010": RegionalParameters(
                "ADRICE2010.csv", "ADRICE2010", regiontype_output
            ),
            "ADRICE2012": RegionalParameters(
                "ADRICE2012.csv", "ADRICE2012", regiontype_output
            ),
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


###########################
#
# The store uses RegionalParameters objects, defined here
#
###########################


class RegionalParameters:
    def __init__(self, filename, regiontype_input, regiontype_output):

        full_filename = os.path.join(
            os.path.dirname(__file__), "../../inputdata/params", filename,
        )
        data_raw = pd.read_csv(full_filename)

        if regiontype_input == regiontype_output:
            self.data = data_raw.set_index("region")
        else:
            # Transform the input regional definition to required output regional definitions
            try:
                region_mapper = REGION_MAPPERS[(regiontype_input, regiontype_output)]
            except KeyError:
                raise KeyError(
                    f"Region mapper missing between {regiontype_input} and {regiontype_output}"
                )

            self.data = region_mapper.map_regions(
                data_raw, regiontype_input, regiontype_output
            ).set_index("region")

    def get(self, paramname, region):
        return float(self.data.loc[region, paramname])


###########################
#
# Define region mappers
#
###########################


class RegionMapper:
    """
    Maps a region type to a different region type
    (RICE to IMAGE regions for example)
    """

    def __init__(self, regiontype1, regiontype2, mapping_file):
        full_filename = os.path.join(
            os.path.dirname(__file__), "../../inputdata/regions", mapping_file,
        )
        # Read region mapping
        self.mapping = pd.read_csv(full_filename)

        # Check if both region types are present as columns
        if (
            regiontype1 not in self.mapping.columns
            or regiontype2 not in self.mapping.columns
        ):
            raise KeyError(
                "Region mappers: file {} doesn't contain columns {} and {}.".format(
                    mapping_file, regiontype1, regiontype2
                )
            )

    def map_regions(
        self, data: pd.DataFrame, regiontype_from, regiontype_to, region_column="region"
    ):
        # Merge data with mapping region
        data_merged = data.merge(
            self.mapping[[regiontype_from, regiontype_to]],
            left_on=region_column,
            right_on=regiontype_from,
            how="outer",
        ).drop(columns=["region", regiontype_from])

        # Group by region_to (if there are multiple regions mapping to one, take average)
        data_grouped = (
            data_merged.groupby(regiontype_to)
            .mean()
            .reset_index()
            .rename(columns={regiontype_to: "region"})
        )

        return data_grouped


REGION_MAPPERS: typing.Dict[tuple, RegionMapper] = {}


def register_region_mappers(regiontype1, regiontype2, mapping_file):
    mapper = RegionMapper(regiontype1, regiontype2, mapping_file)

    # Save for both regiontype1 to regiontype2 and vice versa
    REGION_MAPPERS[(regiontype1, regiontype2)] = mapper
    REGION_MAPPERS[(regiontype2, regiontype1)] = mapper


register_region_mappers("IMAGE26", "ADRICE2010", "IMAGE26_ADRICE2010.csv")
register_region_mappers("IMAGE26", "ADRICE2012", "IMAGE26_ADRICE2012.csv")
