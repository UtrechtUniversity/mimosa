from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

from mimosa.common import (
    ConcreteModel,
    data,
    regional_params,
    TransformationFactory,
    ModelContext,
)
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.model_builder import ALL_COMPONENTS, create_model
from mimosa.components import emissions
from mimosa.concrete_model import custom_constraints
from mimosa.core.model_inputs import ModelInputs


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
    - Loads the data and prepares explicit input lookup
    - Builds initialized concrete components and collects their equations
    - Performs preprocessing tasks
    """

    concrete_model: ConcreteModel
    equations: list
    parser_tree: dict
    model_context: ModelContext
    inputs: ModelInputs
    _data_store: data.DataStore
    _regional_param_store: regional_params.RegionalParamStore

    def __init__(self, params):
        self._params = params

    def build_model(self):
        """
        Creates the MIMOSA concrete_model based on the provided parameters.
        This method performs the following steps:
        1. Checks and parses the parameters for validity.
        2. Loads the necessary data, regional parameters and input lookup.
        3. Builds the concrete model with initialized inputs and selected modules.
        4. Applies custom constraints and Pyomo transformations.
        5. Fixes initial abatement after variable propagation.

        Returns:
            ModelBuildResult: Named references to the concrete model, parsed
                parameters, simulation equations, and model context.
        """
        self._check_and_parse_params()
        self._data_store, self._regional_param_store = self._load_data()
        self.inputs = self._create_model_inputs()
        self.model_context = self._create_model_context(self.inputs)
        self.concrete_model, self.equations = self._create_model()
        self._apply_custom_constraints()
        self._apply_pyomo_transformations()
        emissions.fix_initial_abatement(self.concrete_model)

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

    def _create_model_inputs(self) -> ModelInputs:
        """Prepare input lookup using the already-loaded stores and config."""
        return ModelInputs(
            params=self.parsed_params,
            parser_tree=self.parser_tree,
            data_store=self._data_store,
            regional_store=self._regional_param_store,
        )

    def _create_model_context(
        self, inputs: Optional[ModelInputs] = None
    ) -> ModelContext:
        model_params = self._params["model structure"]

        return ModelContext(
            components={
                component.name: component.read_config(model_params)
                for component in ALL_COMPONENTS
            },
            inputs=inputs,
        )

    def _create_model(self) -> Tuple[ConcreteModel, List]:
        """Build the selected components directly on a concrete model."""
        return create_model(self.model_context)

    def _load_data(self):
        """
        Loads the data and parameter values for explicit input lookup.
        Returns:
            tuple: (data_store, regional_param_store)
        """
        regional_param_store = regional_params.RegionalParamStore(
            self._params, self.parser_tree
        )
        data_store = data.DataStore(self._params)

        return data_store, regional_param_store

    def _apply_custom_constraints(self) -> None:
        """Apply configured constraints to the initialized concrete model."""
        if self._params.get("custom_constraints") is not None:
            custom_constraints.set_custom_constraints(self.concrete_model, self._params)

    def _apply_pyomo_transformations(self) -> None:
        """
        Apply Pyomo transformations after model construction and customization.

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
