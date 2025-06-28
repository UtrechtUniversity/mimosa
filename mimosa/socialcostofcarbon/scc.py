import numpy as np
import pandas as pd
from collections import namedtuple

from mimosa.common import regional_params, data
from mimosa.concrete_model.instantiate_params import InstantiatedModel
from mimosa.concrete_model.simulation_mode.set_constraints import _get_interp_data
from mimosa.components import sealevelrise
from mimosa.components.damages.coacch import damage_fct


class SCC:
    # pylint: disable=no-member
    def __init__(self, params: dict):
        self.params = params
        self.regions = params["regions"]

        # Create the regional parameter store
        self.regional_param_store = regional_params.RegionalParamStore(self.params)

        # Create the data store
        self.data_store = data.DataStore(self.params, self.regional_param_store)

        self.data_functions = DataFunctions()

        instantiated_model = InstantiatedModel(
            self.data_functions,
            self.regional_param_store,
            self.data_store,
            False,
        )

        # From the instantiated model, only the parameter data ("instance_data")
        # is used. Note that we use the default namespace parameters, "None"
        instance_data = instantiated_model.instance_data[None]
        self.data = dict_to_object(instance_data)

        self.regions = self.data.regions
        self.years_i = list(self.data.t)
        self.years = [self.data_functions.year(i) for i in self.years_i]

        self.check_regional_emissions_input()

        self.calculate_damages()

    def check_regional_emissions_input(self):
        # Check if regional_emissions is given in params["simulation"]["constraint_variables"],
        # then use baseline regional emissions
        try:
            filepath_or_data = self.params["simulation"]["constraint_variables"][
                "regional_emissions"
            ]
            self.override_regional_emissions = True
            data_cache = {}
            interp_data = _get_interp_data(
                filepath_or_data, data_cache, "regional_emissions"
            )
            self.new_regional_emissions = pd.DataFrame(
                {r: interp_data.get(r, self.years) for r in self.regions},
                index=self.years,
            ).T
        except KeyError:
            self.override_regional_emissions = False

    def calculate_damages(self):
        out = {}

        years = self.years
        regions = self.regions

        # 1. Calculate regional emissions and GDP
        if self.override_regional_emissions:
            out["regional_emissions"] = self.new_regional_emissions

        else:
            out["regional_emissions"] = pd.DataFrame(
                {r: self.data_functions.baseline_emissions(years, r) for r in regions},
                index=years,
            ).T

        out["gdp"] = pd.DataFrame(
            {r: self.data_functions.GDP(years, r) for r in regions},
            index=years,
        ).T

        # 2. Calculate global emissions (sum of regional emissions) and cumulative emissions
        out["global_emissions"] = out["regional_emissions"].sum()
        cumulative_emissions = pd.Series(
            {
                year: np.trapezoid(
                    out["global_emissions"][:year],
                    x=out["global_emissions"][:year].index,
                )
                for year in out["global_emissions"].index
            }
        )

        # 3. From this, calculate temperature increase
        T0 = self.data.T0
        TCRE = self.data.TCRE
        out["temperature"] = T0 + TCRE * cumulative_emissions

        # 4. And calculate SLR
        total_slr = pd.Series()
        for t in self.years_i:
            if t == 0:
                slr_thermal = sealevelrise.slr_thermal_expansion_init(self.data)
                slr_cumgsic = 0.015
                slr_cumgis = 0.006
            else:
                prev_temp = out["temperature"][years[t - 1]]
                slr_thermal = sealevelrise.slr_thermal_expansion(
                    slr_thermal, prev_temp, self.data
                )
                slr_cumgsic = sealevelrise.slr_gsic(slr_cumgsic, prev_temp, self.data)
                slr_cumgis = sealevelrise.slr_gis(slr_cumgis, prev_temp, self.data)
            total_slr[years[t]] = slr_thermal + slr_cumgsic + slr_cumgis

        # 5. Calculate regional damages
        out["damages_temperature"] = pd.DataFrame(
            {
                r: self.data.damage_scale_factor
                * damage_fct(
                    out["temperature"] - 0.6,
                    out["temperature"].iloc[0] - 0.6,
                    self.data,
                    r,
                    False,
                )
                for r in regions
            }
        ).T

        out["damages_slr"] = pd.DataFrame(
            {
                r: self.data.damage_scale_factor
                * damage_fct(total_slr, total_slr.iloc[0], self.data, r, True)
                for r in regions
            }
        ).T

        out["damages_total"] = out["damages_temperature"] + out["damages_slr"]
        out["damages_absolute"] = out["damages_total"] * out["gdp"]

        self.output = out


class DataFunctions:
    pass


def dict_to_object(data_dict: dict, name="object"):
    obj = namedtuple(name, data_dict.keys())(
        *[v[None] if list(v.keys()) == [None] else v for v in data_dict.values()]
    )
    return obj
