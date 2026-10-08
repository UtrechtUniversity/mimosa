import pytest

from mimosa.core.helpers import ComponentConfig, ModelContext
from mimosa.core.initializer import ModelBuildResult, Preprocessor


def _model_structure():
    return {
        "damage module": "damage-choice",
        "damage module options": {"adaptation": "combined"},
        "emissiontrade module": "trade-choice",
        "financialtransfer module": "transfer-choice",
        "effortsharing module": "effort-choice",
        "welfare module": "welfare-choice",
        "objective module": "objective-choice",
        "emissions options": {"emissions-option": True},
        "sealevelrise options": {},
        "mitigation options": {"learning": False},
        "cobbdouglas options": {},
    }


def test_create_model_context_separates_registry_and_fixed_components():
    preprocessor = Preprocessor({"model structure": _model_structure()})

    context = preprocessor._create_model_context()

    assert context.components["damage"] == ComponentConfig(
        module="damage-choice",
        options={"adaptation": "combined"},
    )
    assert context.components["objective"].module == "objective-choice"
    assert context.components["emissions"] == ComponentConfig(
        options={"emissions-option": True}
    )
    assert context.components["mitigation"].module == ""
    assert context.inputs is None


def test_build_model_orchestrates_stages_and_returns_their_artifacts(monkeypatch):
    """Verify the build pipeline's order and output without constructing a real model.

    Each build stage is replaced by a small test double that records when it is
    called and returns a unique sentinel object. This isolates the orchestration
    contract: stages must run in the intended order, and ``ModelBuildResult`` must
    contain the exact artifacts produced by those stages.
    """
    preprocessor = Preprocessor({"source": "user parameters"})
    context = ModelContext(components={})
    # Unique objects make accidental substitution or re-creation visible.
    equations = [object()]
    data_store = object()
    regional_store = object()
    concrete_model = object()
    inputs = object()
    calls = []

    def parse_params():
        calls.append("parse")
        preprocessor._params = {"source": "parsed parameters"}

    def create_inputs():
        calls.append("inputs")
        assert preprocessor._data_store is data_store
        assert preprocessor._regional_param_store is regional_store
        return inputs

    def create_context(model_inputs):
        calls.append("context")
        assert model_inputs is inputs
        return context

    def create_model():
        calls.append("concrete model")
        assert preprocessor.model_context is context
        return concrete_model, equations

    def load_data():
        calls.append("load data")
        return data_store, regional_store

    # Replace expensive configuration, data, and Pyomo work with stage spies.
    monkeypatch.setattr(preprocessor, "_check_and_parse_params", parse_params)
    monkeypatch.setattr(preprocessor, "_create_model_context", create_context)
    monkeypatch.setattr(preprocessor, "_create_model_inputs", create_inputs)
    monkeypatch.setattr(preprocessor, "_create_model", create_model)
    monkeypatch.setattr(preprocessor, "_load_data", load_data)
    monkeypatch.setattr(
        preprocessor,
        "_apply_custom_constraints",
        lambda: calls.append("custom constraints"),
    )
    monkeypatch.setattr(
        preprocessor,
        "_apply_pyomo_transformations",
        lambda: calls.append("Pyomo transformations"),
    )
    monkeypatch.setattr(
        "mimosa.core.initializer.emissions.fix_initial_abatement",
        lambda model: calls.append(("initial abatement", model)),
    )

    result = preprocessor.build_model()

    # Custom constraints must be applied to the constructed model before
    # transformations potentially fix or propagate its variables.
    assert calls == [
        "parse",
        "load data",
        "inputs",
        "context",
        "concrete model",
        "custom constraints",
        "Pyomo transformations",
        ("initial abatement", concrete_model),
    ]
    assert result == ModelBuildResult(
        concrete_model=concrete_model,
        params={"source": "parsed parameters"},
        equations=equations,
        context=context,
    )
    # Existing callers may continue to unpack the former three-value result.
    assert tuple(result) == (
        concrete_model,
        {"source": "parsed parameters"},
        equations,
    )


def test_production_build_never_instantiates_an_abstract_model(monkeypatch):
    from mimosa import MIMOSA
    from mimosa.common import AbstractModel, ConcreteModel

    def forbidden(*_args, **_kwargs):
        raise AssertionError("Production must build directly without create_instance")

    monkeypatch.setattr(AbstractModel, "create_instance", forbidden)
    model = MIMOSA({"time": {"end": 2030, "periods": {}}, "regions": {"CAN": {}}})
    assert isinstance(model.concrete_model, ConcreteModel)
    assert not hasattr(model.preprocessor, "_abstract_model")
    assert not hasattr(model.preprocessor, "instantiated_model")
    assert model.concrete_model.nopolicy_damage_costs.extract_values()
    assert model.run_simulation(relative_abatement=0.2).damage_costs.values.shape == (2, 1)


def test_custom_constraints_are_applied_only_when_configured(monkeypatch):
    concrete_model = object()
    calls = []
    preprocessor = Preprocessor({"custom_constraints": {"setting": True}})
    preprocessor.concrete_model = concrete_model

    monkeypatch.setattr(
        "mimosa.core.initializer.custom_constraints.set_custom_constraints",
        lambda model, params: calls.append((model, params)),
    )

    preprocessor._apply_custom_constraints()

    assert calls == [(concrete_model, preprocessor.parsed_params)]

    preprocessor._params = {"custom_constraints": None}
    preprocessor._apply_custom_constraints()
    assert len(calls) == 1


def test_pyomo_transformations_are_applied_in_order(monkeypatch):
    calls = []
    concrete_model = object()
    preprocessor = Preprocessor({"regions": {"A": {}, "B": {}}})
    preprocessor.concrete_model = concrete_model

    class FakeTransformation:
        def __init__(self, name):
            self.name = name

        def apply_to(self, model):
            calls.append((self.name, model))

    monkeypatch.setattr(
        "mimosa.core.initializer.TransformationFactory",
        lambda name: FakeTransformation(name),
    )

    preprocessor._apply_pyomo_transformations()

    assert calls == [
        ("contrib.init_vars_midpoint", concrete_model),
        ("contrib.detect_fixed_vars", concrete_model),
        ("contrib.propagate_fixed_vars", concrete_model),
    ]


def test_pyomo_transformation_failures_are_not_suppressed(monkeypatch):
    preprocessor = Preprocessor({"regions": {"A": {}}})
    preprocessor.concrete_model = object()

    class FailingTransformation:
        def apply_to(self, _model):
            raise RuntimeError("transformation failed")

    monkeypatch.setattr(
        "mimosa.core.initializer.TransformationFactory",
        lambda _name: FailingTransformation(),
    )

    with pytest.raises(RuntimeError, match="transformation failed"):
        preprocessor._apply_pyomo_transformations()
