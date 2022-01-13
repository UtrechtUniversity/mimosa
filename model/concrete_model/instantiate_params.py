import numpy as np
from model.common import AbstractModel, units
from model.common.data import DataStore
from model.common.regional_params import RegionalParamStore

# Util to create a None-indexed dictionary for scalar components
# (see https://pyomo.readthedocs.io/en/stable/working_abstractmodels/data/raw_dicts.html)
V = lambda val: {None: val}


class InstantiatedModel:
    def __init__(
        self,
        abstract_model: AbstractModel,
        regional_param_store: RegionalParamStore,
        data_store: DataStore,
        quant: units.Quantity,
        create_concrete_model: bool = True,
    ):

        self.abstract_model = abstract_model
        self.regional_param_store = regional_param_store
        self.data_store = data_store
        self.quant = quant

        # Get the non-regional params (from config.yaml) from the RegionalParamStore
        self.params = regional_param_store.params

        # First, set the data functions in the abstract model
        self.set_data_functions()

        self.instance_data = self.get_param_values()

        if create_concrete_model:
            self.concrete_model = self.create_instance()

    def set_data_functions(self):
        # The data functions need to be changed in the abstract model
        # before initialization.
        self.abstract_model.baseline_emissions = self.data_store.data_object("baseline")
        self.abstract_model.population = (
            self.abstract_model.L
        ) = self.data_store.data_object("population")
        self.abstract_model.GDP = self.data_store.data_object("GDP")
        self.abstract_model.carbon_intensity = self.data_store.data_object(
            "carbon_intensity"
        )
        self.abstract_model.TFP = self.data_store.data_object("TFP")

    def create_instance(self):
        return self.abstract_model.create_instance(self.instance_data)

    def get_param_values(self):

        damage_module = self.params["model"]["damage module"]

        instance_data = {None: {}}

        # Main instance data
        self._set_instance_data_main(instance_data)

        # Instance data for RICE2010 damage/adaptation:
        if damage_module == "RICE2010":
            self._set_instance_data_rice2010(instance_data)

        # Instance data for RICE2012 damage/adaptation:
        if damage_module == "RICE2012":
            self._set_instance_data_rice2012(instance_data)

        # Instance data for COACCH damages:
        if damage_module == "COACCH":
            self._set_instance_data_coacch(instance_data)

        # For WITCH damage/adaption:
        # if damage_module == "WITCH":
        #     instance_data[None].update(self._instance_data_witch())

        # Raise warning for partially irreversible damages when damage module != RICE2010:
        if (
            damage_module == "RICE2010"
            and self.params["economics"]["damages"]["percentage reversible"] != 1
        ):
            raise NotImplementedError(
                'Partially irreversible damages not implemented for damage module "{}"'.format(
                    damage_module
                )
            )

        return instance_data

    ########################
    #
    # Private functions
    #
    ########################

    def _set_instance_data_main(self, instance_data) -> None:

        params = self.params
        quant = self.quant

        t_start = params["time"]["start"]
        t_end = params["time"]["end"]
        dt = params["time"]["dt"]
        num_years = int(np.ceil((t_end - t_start) / dt)) + 1
        self.abstract_model.year = lambda t: t_start + t * dt
        year2100 = int((2100 - t_start) / dt)

        parameter_mapping = {
            "beginyear": V(t_start),
            "dt": V(dt),
            "tf": V(num_years - 1),
            "t": V(range(num_years)),
            "year2100": V(year2100),
            "regions": V(params["regions"].keys()),
            "baseline_carbon_intensity": V(
                params["emissions"]["baseline carbon intensity"]
            ),
            "budget": V(quant(params["emissions"]["carbonbudget"], "emissions_unit")),
            "inertia_regional": V(params["emissions"]["inertia"]["regional"]),
            "inertia_global": V(params["emissions"]["inertia"]["global"]),
            "global_min_level": V(
                quant(params["emissions"]["global min level"], "emissionsrate_unit")
            ),
            "regional_min_level": V(
                quant(params["emissions"]["regional min level"], "emissionsrate_unit")
            ),
            "no_pos_emissions_after_budget_year": V(
                params["emissions"]["not positive after budget year"]
            ),
            "non_increasing_emissions_after_2100": V(
                params["emissions"]["non increasing emissions after 2100"]
            ),
            "T0": V(quant(params["temperature"]["initial"], "temperature_unit")),
            "temperature_target": V(
                quant(params["temperature"]["target"], "temperature_unit")
            ),
            "TCRE": V(
                quant(
                    params["temperature"]["TCRE"],
                    "(temperature_unit)/(emissions_unit)",
                )
            ),
            "LBD_rate": V(params["economics"]["MAC"]["rho"]),
            "LBD_scaling": V(quant("40 GtCO2", "emissions_unit")),
            "LOT_rate": V(0),
            "damage_scale_factor": V(params["economics"]["damages"]["scale factor"]),
            "fixed_adaptation": V(params["economics"]["adaptation"]["fixed"]),
            "perc_reversible_damages": V(
                params["economics"]["damages"]["percentage reversible"]
            ),
            "ignore_damages": V(params["economics"]["damages"]["ignore damages"]),
            "MAC_gamma": V(
                quant(
                    params["economics"]["MAC"]["gamma"],
                    "currency_unit/emissionsrate_unit",
                )
            ),
            "MAC_beta": V(params["economics"]["MAC"]["beta"]),
            "MAC_scaling_factor": self.regional_param_store.get("MAC", "kappa"),
            "init_capitalstock_factor": self.regional_param_store.get(
                "economics", "init_capital_factor"
            ),
            "alpha": V(params["economics"]["GDP"]["alpha"]),
            "dk": V(params["economics"]["GDP"]["depreciation of capital"]),
            "sr": V(params["economics"]["GDP"]["savings rate"]),
            "elasmu": V(params["economics"]["elasmu"]),
            "PRTP": V(params["economics"]["PRTP"]),
            "allow_trade": V(params["model"]["allow trade"]),
        }

        instance_data[None].update(parameter_mapping)

        # Set sea level rise parameters
        self._set_instance_data_slr(instance_data)

    def _set_instance_data_slr(self, instance_data) -> None:
        parameter_mapping = {
            # Sea level rise:
            "slr_thermal_equil": V(0.5),  # Equilibrium
            "slr_thermal_init": V(0.0920666936642),  # Initial condition
            "slr_thermal_adjust_rate": V(0.024076141150722),  # Adjustment rate
            "slr_gsic_melt_rate": V(0.0008),  # Melt rate
            "slr_gsic_total_ice": V(0.26),  # Total ice
            "slr_gsic_equil_temp": V(-1),  # Equil temp
            "slr_gis_melt_rate_above_thresh": V(1.11860082),  # Melt rate above threshol
            "slr_gis_init_melt_rate": V(0.6),  # Initial melt rate
            "slr_gis_init_ice_vol": V(7.3),  # Initial ice volume
        }

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_rice2010(self, instance_data) -> None:
        params = self.params
        parameter_mapping = {
            "adapt_curr_level": V(params["economics"]["adaptation"]["curr_level"]),
            "damage_a1": self.regional_param_store.get("ADRICE2010", "a1"),
            "damage_a2": self.regional_param_store.get("ADRICE2010", "a2"),
            "damage_a3": self.regional_param_store.get("ADRICE2010", "a3"),
            "adapt_g1": self.regional_param_store.get("ADRICE2010", "g1"),
            "adapt_g2": self.regional_param_store.get("ADRICE2010", "g2"),
        }

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_rice2012(self, instance_data) -> None:
        parameter_mapping = {
            "damage_a1": self.regional_param_store.get("ADRICE2012", "a1"),
            "damage_a2": self.regional_param_store.get("ADRICE2012", "a2"),
            "damage_a3": self.regional_param_store.get("ADRICE2012", "a3"),
            "adap1": self.regional_param_store.get("ADRICE2012", "nu1"),
            "adap2": self.regional_param_store.get("ADRICE2012", "nu2"),
            "adap3": self.regional_param_store.get("ADRICE2012", "nu3"),
            "adapt_rho": V(0.5),
            "SLRdam1": self.regional_param_store.get("ADRICE2012", "slrdam1"),
            "SLRdam2": self.regional_param_store.get("ADRICE2012", "slrdam2"),
        }

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_coacch(self, instance_data) -> None:

        try:
            damage_quantile = self.params["economics"]["damages"]["quantile"]
        except KeyError:
            damage_quantile = 0.5

        combined_slr_nonslr_damages = self.params["economics"]["damages"][
            "coacch_combined_slr_nonslr_damages"
        ]
        slr_adapt_param = self.params["economics"]["damages"]["coacch_slr_adapt"]

        V_region = lambda x: {region: x for region in self.params["regions"]}

        if combined_slr_nonslr_damages:
            adapt_prfx = "Ad" if slr_adapt_param == 1 else "NoAd"
            if slr_adapt_param not in [0, 1]:
                raise NotImplementedError(
                    "COACCH combined damages with adaptation that is not equal to 0 or to 1 is not implemented."
                )
            parameter_mapping = {
                # Combined non-SLR and SLR damages are always quadratic
                "damage_noslr_form": V_region("Robust-Quadratic"),
                "damage_noslr_b1": self.regional_param_store.get(
                    "COACCH", f"combined_b1_{adapt_prfx}-q{damage_quantile}"
                ),
                "damage_noslr_b2": self.regional_param_store.get(
                    "COACCH", f"combined_b2_{adapt_prfx}-q{damage_quantile}"
                ),
                "damage_noslr_b3": V_region(0),
                "damage_noslr_a": V_region(1),
                # SLR damages (zero but need to be defined)
                "damage_slr_form_opt_adapt": V_region("Robust-Linear"),
                "damage_slr_form_no_adapt": V_region("Robust-Linear"),
                "damage_slr_b1_opt_adapt": V_region(0),
                "damage_slr_b1_no_adapt": V_region(0),
                "damage_slr_b2_opt_adapt": V_region(0),
                "damage_slr_b2_no_adapt": V_region(0),
                "damage_slr_b3_opt_adapt": V_region(0),
                "damage_slr_b3_no_adapt": V_region(0),
                "damage_slr_a_opt_adapt": V_region(0),
                "damage_slr_a_no_adapt": V_region(0),
                "SLR_adapt_param": V(slr_adapt_param),
            }

        else:

            factor_noslr = f"NoSLR_a (q={damage_quantile})"

            parameter_mapping = {
                # Non-SLR damages:
                "damage_noslr_form": self.regional_param_store.get(
                    "COACCH", "NoSLR_form"
                ),
                "damage_noslr_b1": self.regional_param_store.get("COACCH", "NoSLR_b1"),
                "damage_noslr_b2": self.regional_param_store.get("COACCH", "NoSLR_b2"),
                "damage_noslr_b3": self.regional_param_store.get("COACCH", "NoSLR_b3"),
                "damage_noslr_a": self.regional_param_store.get("COACCH", factor_noslr),
                "SLR_adapt_param": V(slr_adapt_param),
            }

            # SLR damages:
            for slr_adapt in ["opt", "no"]:
                adapt_prfx = "Ad" if slr_adapt == "opt" else "NoAd"
                prfx = f"SLR-{adapt_prfx}"
                factor_slr_ad = f"{prfx}_a (q={damage_quantile})"

                parameter_mapping.update(
                    {
                        # First, optimal adaptation damages:
                        f"damage_slr_form_{slr_adapt}_adapt": self.regional_param_store.get(
                            "COACCH", f"{prfx}_form"
                        ),
                        f"damage_slr_b1_{slr_adapt}_adapt": self.regional_param_store.get(
                            "COACCH", f"{prfx}_b1"
                        ),
                        f"damage_slr_b2_{slr_adapt}_adapt": self.regional_param_store.get(
                            "COACCH", f"{prfx}_b2"
                        ),
                        f"damage_slr_b3_{slr_adapt}_adapt": self.regional_param_store.get(
                            "COACCH", f"{prfx}_b3"
                        ),
                        f"damage_slr_a_{slr_adapt}_adapt": self.regional_param_store.get(
                            "COACCH", factor_slr_ad
                        ),
                    }
                )

            parameter_mapping.update(
                {
                    "adapt_costs_g1": self.regional_param_store.get("ADRICE2010", "g1"),
                    "adapt_costs_g2": self.regional_param_store.get("ADRICE2010", "g2"),
                }
            )

        instance_data[None].update(parameter_mapping)

    # def _instance_data_witch(self) -> dict:
    #     return {
    #         "damage_omega1_pos": self.data_store.get_regional("damages", "omega1_pos"),
    #         "damage_omega1_neg": self.data_store.get_regional("damages", "omega1_neg"),
    #         "damage_omega2_pos": self.data_store.get_regional("damages", "omega2_pos"),
    #         "damage_omega2_neg": self.data_store.get_regional("damages", "omega2_neg"),
    #         "damage_omega3_pos": self.data_store.get_regional("damages", "omega3_pos"),
    #         "damage_omega3_neg": self.data_store.get_regional("damages", "omega3_neg"),
    #         "damage_omega4_pos": self.data_store.get_regional("damages", "omega4_pos"),
    #         "damage_omega4_neg": self.data_store.get_regional("damages", "omega4_neg"),
    #         "adapt_omega_eff_ada": self.data_store.get_regional(
    #             "adaptation", "omega_eff_ada"
    #         ),
    #         "adapt_omega_act": self.data_store.get_regional("adaptation", "omega_act"),
    #         "adapt_omega_eff_act": self.data_store.get_regional(
    #             "adaptation", "omega_eff_act"
    #         ),
    #         "adapt_omega_rada": self.data_store.get_regional(
    #             "adaptation", "omega_rada"
    #         ),
    #         "adapt_rho_ada": self.data_store.get_regional("adaptation", "rho_ada"),
    #         "adapt_rho_act": self.data_store.get_regional("adaptation", "rho_act"),
    #         "adapt_eps": self.data_store.get_regional("adaptation", "eps"),
    #     }
