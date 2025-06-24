from mimosa.common import (
    AbstractModel,
    ConcreteModel,
    data,
    regional_params,
    TransformationFactory,
)
from mimosa.common.config.parseconfig import check_params, parse_param_values
from mimosa.abstract_model import create_abstract_model
from mimosa.concrete_model.instantiate_params import InstantiatedModel
from mimosa.concrete_model import simulation_mode


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
    _abstract_model: AbstractModel
    _data_store: data.DataStore
    _regional_param_store: regional_params.RegionalParamStore

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
        5. Preprocesses the Pyomo model by aggregating identical variables and more
        Returns:
            ConcreteModel: The instantiated model ready for simulation.
        """
        self._check_and_parse_params()
        self._abstract_model, self.equations = self._create_abstract_model()
        self._data_store, self._regional_param_store = self._load_data()
        self.concrete_model = self._instantiate_model()
        self._preprocess_pyomo_model()
        return self.concrete_model, self.parsed_params, self.equations

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

    def _create_abstract_model(self) -> AbstractModel:
        """
        Loads all the equations and creates an abstract_model.
        `abstract` here means that the model is not yet instantiated with data.

        Returns:
            AbstractModel: model corresponding to the damage/objective module combination
        """
        damage_module = self._params["model"]["damage module"]
        emissiontrade_module = self._params["model"]["emissiontrade module"]
        financialtransfer_module = self._params["model"]["financialtransfer module"]
        welfare_module = self._params["model"]["welfare module"]
        objective_module = self._params["model"]["objective module"]
        effortsharing_regime = self._params["effort sharing"]["regime"]

        return create_abstract_model(
            damage_module,
            emissiontrade_module,
            financialtransfer_module,
            welfare_module,
            objective_module,
            effortsharing_regime,
        )

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
        instantiated_model = InstantiatedModel(
            self._abstract_model, self._regional_param_store, self._data_store
        )
        m = instantiated_model.concrete_model

        # When using simulation mode, add extra constraints to variables and disable other constraints
        if (
            self._params.get("simulation") is not None
            and self._params["simulation"]["simulationmode"]
        ):
            simulation_mode.set_simulation_mode(m, self._params)

        return m

    def _preprocess_pyomo_model(self) -> None:
        """
        Pyomo can apply certain pre-processing steps before sending the model
        to the solver. These include:
          - Aggregate variables that are linked by equality constraints
          - Initialise non-fixed variables to midpoint of their boundaries
          - Fix variables that are de-facto fixed
          - Propagate variable fixing for equalities of type x = y
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
