from dataclasses import dataclass
from typing import Iterator

from mimosa.common import (
    AbstractModel,
    ConcreteModel,
    data,
    regional_params,
    TransformationFactory,
    ModelContext,
    ComponentConfig,
)
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.abstract_model import create_abstract_model
from mimosa.concrete_model.instantiate_params import InstantiatedModel
from mimosa.concrete_model import custom_constraints


@dataclass(frozen=True)
class ModelBuildResult:
    """Named outputs of the model-construction pipeline."""

    concrete_model: ConcreteModel
    params: dict
    equations: list
    context: ModelContext

    def __iter__(self) -> Iterator:
        """Preserve the former three-value tuple-unpacking interface."""
        yield self.concrete_model
        yield self.params
        yield self.equations


class Preprocessor:
    """
    Handles the initialization of the MIMOSA model:
    - Checks parameters for validity
    - Loads all the equations and creates an abstract model
    - Loads the data and parameter values to instantiate the model
    - Performs preprocessing tasks
    """

    concrete_model: ConcreteModel
    equations: list
    parser_tree: dict
    model_context: ModelContext
    _abstract_model: AbstractModel
    _data_store: data.DataStore
    _regional_param_store: regional_params.RegionalParamStore
    instantiated_model: InstantiatedModel

    def __init__(self, params):
        self._params = params

    def build_model(self):
        """
        Creates the MIMOSA concrete_model based on the provided parameters.
        This method performs the following steps:
        1. Checks and parses the parameters for validity.
        2. Creates an abstract model based on the specified modules.
        3. Loads the necessary data and regional parameters.
        4. Instantiates the abstract model with the loaded data and parameters.
        5. Applies custom constraints and Pyomo transformations.

        Returns:
            ModelBuildResult: Named references to the concrete model, parsed
                parameters, simulation equations, and model context.
        """
        self._check_and_parse_params()
        self.model_context = self._create_model_context()
        self._abstract_model, self.equations = self._create_abstract_model()
        self._data_store, self._regional_param_store = self._load_data()
        self.concrete_model = self._instantiate_model()
        self._apply_custom_constraints()
        self._apply_pyomo_transformations()

        return ModelBuildResult(
            concrete_model=self.concrete_model,
            params=self.parsed_params,
            equations=self.equations,
            context=self.model_context,
        )

    @property
    def parsed_params(self):
        """Returns the parsed parameters."""
        return self._params

    def _check_and_parse_params(self):
        """
        Checks the parameters for validity.
        Raises a RuntimeWarning if any parameter is invalid.
        """
        # Check for validity
        params, parser_tree = check_params(self._params, True)

        # Parse parameter for references to other parameters
        params = parse_param_values(params)

        # Save parsed params and parser tree
        self._params = params
        self.parser_tree = parser_tree

    def _create_model_context(self) -> ModelContext:
        model_params = self._params["model structure"]

        def registry_component(name):
            return ComponentConfig(
                module=model_params[f"{name} module"],
                options=model_params.get(f"{name} module options", {}),
            )

        def fixed_component(name):
            return ComponentConfig(
                options=model_params.get(f"{name} options", {}),
            )

        return ModelContext(
            components={
                "damage": registry_component("damage"),
                "emissiontrade": registry_component("emissiontrade"),
                "financialtransfer": registry_component("financialtransfer"),
                "effortsharing": registry_component("effortsharing"),
                "welfare": registry_component("welfare"),
                "objective": registry_component("objective"),
                # Fixed/non-registry components
                "emissions": fixed_component("emissions"),
                "sealevelrise": fixed_component("sealevelrise"),
                "mitigation": fixed_component("mitigation"),
                "cobbdouglas": fixed_component("cobbdouglas"),
            }
        )

    def _create_abstract_model(self) -> AbstractModel:
        """
        Loads all the equations and creates an abstract_model.
        `abstract` here means that the model is not yet instantiated with data.

        Returns:
            AbstractModel: model corresponding to the damage/objective module combination
        """
        return create_abstract_model(self.model_context)

    def _load_data(self):
        """
        Loads the data and parameter values to instantiate the model.
        Returns:
            tuple: (data_store, regional_param_store)
        """
        regional_param_store = regional_params.RegionalParamStore(
            self._params, self.parser_tree
        )
        data_store = data.DataStore(self._params)

        return data_store, regional_param_store

    def _instantiate_model(self) -> ConcreteModel:
        """
        Instantiates the abstract model with the data and parameters.
        Returns:
            ConcreteModel: instantiated model ready for simulation
        """
        self.instantiated_model = InstantiatedModel(
            self._abstract_model, self._regional_param_store, self._data_store
        )
        return self.instantiated_model.concrete_model

    def _apply_custom_constraints(self) -> None:
        """Apply configured constraints to the instantiated concrete model."""
        if self._params.get("custom_constraints") is not None:
            custom_constraints.set_custom_constraints(
                self.concrete_model, self._params
            )

    def _apply_pyomo_transformations(self) -> None:
        """
        Apply Pyomo transformations after model instantiation and customization.

        These transformations initialize non-fixed variables to the midpoint of
        their bounds, detect de-facto fixed variables, and, for multi-region
        models, propagate variable fixing through equalities.
        """
        more_than_one_region = len(self._params["regions"]) > 1

        TransformationFactory("contrib.init_vars_midpoint").apply_to(
            self.concrete_model
        )
        TransformationFactory("contrib.detect_fixed_vars").apply_to(self.concrete_model)
        if more_than_one_region:
            TransformationFactory("contrib.propagate_fixed_vars").apply_to(
                self.concrete_model
            )
