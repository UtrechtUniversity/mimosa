"""Define region mappers, used to transform one regional definition to another.

Currently, only `mean` is used. In future versions, this will be extended
and automatic region mapping will be used by transforming to country level first."""

import os
import pandas as pd


class RegionMapper:
    """
    Maps a region type to a different region type
    (RICE to IMAGE regions for example)
    """

    def __init__(self, regiontype1, regiontype2, mapping_file):
        full_filename = os.path.join(
            os.path.dirname(__file__),
            "../../",
            mapping_file,
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

        # Group by region_to (if there are multiple regions mapping to one,
        # take average, or the first value for non-numeric columns)
        aggregation_methods = {
            col_name: "mean" if pd.api.types.is_numeric_dtype(column) else "first"
            for col_name, column in data_merged.items()
            if col_name != regiontype_to
        }
        data_grouped = (
            data_merged.groupby(regiontype_to)
            .agg(aggregation_methods)
            .reset_index()
            .rename(columns={regiontype_to: "region"})
        )

        return data_grouped
