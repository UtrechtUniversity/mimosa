from dataclasses import dataclass
from typing import Iterator, List, Tuple

from mimosa.common import (
    AbstractModel,
    ConcreteModel,
    data,
    regional_params,
    TransformationFactory,
    ModelContext,
)
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.abstract_model import ALL_COMPONENTS, create_abstract_model
from mimosa.components.sealevelrise import slr_initial_value
from mimosa.concrete_model.instantiate_params import InstantiatedModel
from mimosa.concrete_model import custom_constraints
from pyomo.environ import value


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
        self._fix_pilot_initial_conditions()
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

        return ModelContext(
            components={
                component.name: component.read_config(model_params)
                for component in ALL_COMPONENTS
            }
        )

    def _create_abstract_model(self) -> Tuple[AbstractModel, List]:
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

    def _fix_pilot_initial_conditions(self) -> None:
        """Fix a small pilot set of state variables at the initial timestep.

        This deliberately lives in the preprocessor for now.  The indexed variables,
        regions, and parameter values do not exist while the AbstractModel is being
        assembled, so parameter-dependent initial values can only be fixed after
        ``create_instance`` has returned the concrete model.
        """
        m = self.concrete_model

        m.global_cumulative_emissions[0].fix(0)

        for r in m.regions:
            m.capital_stock[0, r].fix(
                value(m.init_capitalstock_factor[r] * m.baseline_GDP[0, r])
            )

        slr_initial_conditions = {
            "slr_thermal_fast": slr_initial_value(m.slr_thermal_fast_init, m),
            "slr_thermal_slow": slr_initial_value(m.slr_thermal_slow_init, m),
            "slr_cumgsic": slr_initial_value(m.slr_gsic_init, m),
            "slr_cumgis": slr_initial_value(m.slr_gis_init, m),
            "slr_antarctic_ocean_temp": slr_initial_value(
                m.slr_ais_ocean_temp_init, m
            ),
            "slr_cumais": slr_initial_value(m.slr_ais_init, m),
            "slr_cumlws": 0,
        }
        for variable_name, initial_value in slr_initial_conditions.items():
            getattr(m, variable_name)[0].fix(value(initial_value))

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
