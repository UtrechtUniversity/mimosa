"""The store uses RegionalParameters objects, defined here"""

import os
import pandas as pd


class RegionalParamContainer:
    def __init__(self, filename, regiontype_input, regiontype_output, region_mappers):
        full_filename = os.path.join(
            os.path.dirname(__file__),
            "../../",
            filename,
        )
        data_raw = pd.read_csv(full_filename)

        if regiontype_input == regiontype_output:
            self.data = data_raw.set_index("region")
        else:
            # Transform the input regional definition to required output regional definitions
            try:
                region_mapper = region_mappers[(regiontype_input, regiontype_output)]
            except KeyError as exc:
                raise KeyError(
                    f"Region mapper missing between {regiontype_input} and {regiontype_output}"
                ) from exc

            self.data = region_mapper.map_regions(
                data_raw, regiontype_input, regiontype_output
            ).set_index("region")

    def get(self, paramname, region):
        value = self.data.loc[region, paramname]
        try:
            return float(value)
        except ValueError:
            # If unable to convert to float:
            return value
