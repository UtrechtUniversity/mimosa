import numpy as np

from mimosa.common import AbstractModel, quant, PyomoParam
from mimosa.common.data import DataStore
from mimosa.common.regional_params import RegionalParamStore
from mimosa.common.config.parseconfig import get_nested
from mimosa.common.timegrid import create_time_grid

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

        self.instance_data = self.get_param_values()

        if create_concrete_model:
            self.concrete_model = self.create_instance()

    def create_instance(self):
        return self.abstract_model.create_instance(self.instance_data)

    def get_param_values(self):
        instance_data = {None: {}}

        ## Main instance data
        self._set_instance_data_main(instance_data)

        return instance_data

    ########################
    #
    # Private functions
    #
    ########################

    def _set_instance_data_main(self, instance_data) -> None:
        params = self.params
        t_start = params["time"]["start"]
        time_grid = create_time_grid(params["time"])
        years = np.asarray(time_grid.years)
        num_years = len(years)
        self.abstract_model.year = lambda t: years[t]

        parameter_mapping = {}

        # Attempt to set parameter values automatically from their doc value
        for parameter in self.abstract_model.component_objects(PyomoParam):
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

            ### Time and regional dependent parameter, from data store
            if parameter_doc_str.startswith("timeandregional::"):
                var_name = parameter_doc_str.split("::")[1]
                parameter_mapping[parameter.name] = {
                    (t, r): self.data_store.interp_data(
                        self.abstract_model.year(t), r, var_name
                    )
                    for t in range(num_years)
                    for r in params["regions"].keys()
                }

        parameter_mapping_manual = {
            "beginyear": V(t_start),
            "tf": V(num_years - 1),
            "t": V(range(num_years)),
            "period_length": dict(enumerate(time_grid.period_lengths)),
            "regions": V(params["regions"].keys()),
        }
        parameter_mapping.update(parameter_mapping_manual)

        # Set time-dependent MAC calibration factor, depending on the SSP:
        parameter_mapping["MAC_SSP_calibration_factor"] = {
            t: self.data_store.interp_data_from_dict(
                self.abstract_model.year(t),
                params["economics"]["MAC"]["SSP_calibration_factor"][params["SSP"]],
            )
            for t in range(num_years)
        }

        instance_data[None].update(parameter_mapping)
