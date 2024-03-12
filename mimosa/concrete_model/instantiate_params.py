import numpy as np
from mimosa.common import AbstractModel, quant, Param
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.common.config.parseconfig import get_nested

# Util to create a None-indexed dictionary for scalar components
# (see https://pyomo.readthedocs.io/en/stable/working_abstractmodels/data/raw_dicts.html)
V = lambda val: {None: val}


class InstantiatedModel:
    def __init__(
        self,
        abstract_model: AbstractModel,
        regional_param_store: RegionalParamStore,
        data_store: DataStore,
        create_concrete_model: bool = True,
    ):
        self.abstract_model = abstract_model
        self.regional_param_store = regional_param_store
        self.data_store = data_store

        # Get the non-regional params (from config.yaml) from the RegionalParamStore
        self.params = regional_param_store.params
        self.param_parser_tree = regional_param_store.param_parser_tree

        # First, set the data functions in the abstract model
        self.set_data_functions()

        self.instance_data = self.get_param_values()

        if create_concrete_model:
            self.concrete_model = self.create_instance()

    def set_data_functions(self):
        # The data functions need to be changed in the abstract model
        # before initialization.
        self.abstract_model.baseline_emissions = self.data_store.data_object("baseline")
        self.abstract_model.population = self.abstract_model.L = (
            self.data_store.data_object("population")
        )
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

        ## Main instance data
        self._set_instance_data_main(instance_data)

        ## Damage module:

        # Instance data for RICE2010 damage/adaptation:
        if damage_module == "RICE2010":
            self._set_instance_data_rice2010(instance_data)

        # Instance data for COACCH damages:
        if damage_module == "COACCH":
            # Only used if combined damage function is used,
            # otherwise, the parameter values are set dynamically
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
        t_start = params["time"]["start"]
        t_end = params["time"]["end"]
        dt = params["time"]["dt"]
        num_years = int(np.ceil((t_end - t_start) / dt)) + 1
        self.abstract_model.year = lambda t: t_start + t * dt
        year2100 = int((2100 - t_start) / dt)

        parameter_mapping = {}

        # Attempt to set parameter values automatically from their doc value
        for parameter in self.abstract_model.component_objects(Param):
            # First check if the parameter is callable: in this case,
            # the parameter doc is a function that returns the parameter doc string.
            # This is used for dynamic parameter values (depending on other parameters).
            # If this is the case, give `params` to the function.

            if callable(parameter.doc):
                parameter_doc_str = parameter.doc(params)
            else:
                parameter_doc_str = str(parameter.doc)

            ### Normal parameter, get directly from parameter dictionary
            if parameter_doc_str.startswith("::"):
                keys = parameter_doc_str.split("::")[1].split(".")
                value = get_nested(params, keys)
                # Check type of parameter
                parser = get_nested(self.param_parser_tree, keys)
                if parser.type == "quantity":
                    value = quant(value, parser.unit)
                parameter_mapping[parameter.name] = V(value)

            ### Regional parameter, get from regional parameter store
            if parameter_doc_str.startswith("regional::"):
                param_category, param_name = parameter_doc_str.split("::")[1].split(
                    ".", 1
                )
                parameter_mapping[parameter.name] = self.regional_param_store.get(
                    param_category, param_name
                )

        parameter_mapping_manual = {
            "beginyear": V(t_start),
            "dt": V(dt),
            "tf": V(num_years - 1),
            "t": V(range(num_years)),
            "year2100": V(year2100),
            "regions": V(params["regions"].keys()),
            "LBD_scaling": V(quant("40 GtCO2", "emissions_unit")),
            "LOT_rate": V(0),
            "fixed_adaptation": V(params["economics"]["adaptation"]["fixed"]),
        }

        parameter_mapping.update(parameter_mapping_manual)

        if "custom_mapping" in params["simulation"]:
            parameter_mapping.update(params["simulation"]["custom_mapping"])

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_rice2010(self, instance_data) -> None:
        params = self.params
        parameter_mapping = {
            "adapt_curr_level": V(params["economics"]["adaptation"]["curr_level"]),
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
        slr_withadapt = self.params["economics"]["damages"]["coacch_slr_withadapt"]
        adapt_prfx = "Ad" if slr_withadapt else "NoAd"

        V_region = lambda x: {region: x for region in self.params["regions"]}

        if combined_slr_nonslr_damages:
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
                "damage_slr_form": V_region("Robust-Linear"),
                "damage_slr_b1": V_region(0),
                "damage_slr_b2": V_region(0),
                "damage_slr_b3": V_region(0),
                "damage_slr_a": V_region(0),
            }

        else:

            parameter_mapping = {
                # SLR damages:
            }

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
