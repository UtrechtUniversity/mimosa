import pytest

from mimosa.model_builder import (
    ALL_COMPONENTS,
    MODEL_COMPONENTS,
    OBJECTIVE_COMPONENT,
)
from mimosa.core.component_definition import (
    ComponentDefinition,
    validate_unique_component_names,
)
from types import SimpleNamespace


def test_catalogue_contains_components_in_construction_order():
    """Keep the model's component inventory and construction order visible."""
    assert [component.name for component in MODEL_COMPONENTS] == [
        "emissions",
        "sealevelrise",
        "damage",
        "mitigation",
        "emissiontrade",
        "financialtransfer",
        "effortsharing",
        "cobbdouglas",
        "welfare",
    ]
    assert ALL_COMPONENTS == MODEL_COMPONENTS + (OBJECTIVE_COMPONENT,)
    assert OBJECTIVE_COMPONENT.name == "objective"


def test_component_definition_builds_fixed_and_selected_components():
    calls = []

    def record_fixed(model, inputs):
        calls.append(("fixed", model, inputs))
        return ["fixed constraint"]

    def record_selected(model, inputs):
        calls.append(("selected", model, inputs))
        return ["selected constraint"]

    fixed = ComponentDefinition(name="fixed", get_constraints=record_fixed)
    selectable = ComponentDefinition(
        name="selectable",
        modules={"chosen": record_selected},
    )
    config_calls = []

    def config_value(path):
        config_calls.append(path)
        return "chosen"

    inputs = SimpleNamespace(config_value=config_value)
    model = object()

    assert fixed.build(model, inputs) == ["fixed constraint"]
    assert selectable.build(model, inputs) == ["selected constraint"]
    assert calls == [
        ("fixed", model, inputs),
        ("selected", model, inputs),
    ]
    assert config_calls == ["model structure.selectable module"]


def test_selectable_component_reports_unknown_module_from_config():
    component = ComponentDefinition(
        name="damage", modules={"known": lambda *_args: []}
    )
    inputs = SimpleNamespace(config_value=lambda _path: "unknown")
    with pytest.raises(NotImplementedError, match="Module `unknown` not implemented.*known"):
        component.build(object(), inputs)


def test_component_definition_requires_one_construction_method():
    with pytest.raises(ValueError, match="either get_constraints or selectable modules"):
        ComponentDefinition(name="missing")

    with pytest.raises(ValueError, match="either get_constraints or selectable modules"):
        ComponentDefinition(
            name="ambiguous",
            get_constraints=lambda *_args: [],
            modules={"choice": lambda *_args: []},
        )


def test_component_catalogue_rejects_duplicate_names():
    first = ComponentDefinition(name="duplicate", get_constraints=lambda *_args: [])
    second = ComponentDefinition(name="duplicate", get_constraints=lambda *_args: [])

    with pytest.raises(ValueError, match="Duplicate component names.*duplicate"):
        validate_unique_component_names([first, second])
