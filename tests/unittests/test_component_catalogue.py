import pytest

from mimosa.abstract_model import (
    ALL_COMPONENTS,
    MODEL_COMPONENTS,
    OBJECTIVE_COMPONENT,
)
from mimosa.core.component_definition import (
    ComponentDefinition,
    validate_unique_component_names,
)
from mimosa.core.helpers import ComponentConfig, ModelContext


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


def test_component_definition_uses_the_matching_config_naming_convention():
    fixed = ComponentDefinition(name="fixed", get_constraints=lambda *_args: [])
    selectable = ComponentDefinition(
        name="selectable",
        modules={"chosen": lambda *_args: []},
    )
    model_structure = {
        "fixed options": {"fixed option": True},
        "selectable module": "chosen",
        "selectable module options": {"selectable option": True},
    }

    assert fixed.read_config(model_structure) == ComponentConfig(
        options={"fixed option": True}
    )
    assert selectable.read_config(model_structure) == ComponentConfig(
        module="chosen",
        options={"selectable option": True},
    )


def test_component_definition_builds_fixed_and_selected_components():
    calls = []

    def record_fixed(model, context):
        calls.append(("fixed", model, context))
        return ["fixed constraint"]

    def record_selected(model, context):
        calls.append(("selected", model, context))
        return ["selected constraint"]

    fixed = ComponentDefinition(name="fixed", get_constraints=record_fixed)
    selectable = ComponentDefinition(
        name="selectable",
        modules={"chosen": record_selected},
    )
    context = ModelContext(
        components={
            "fixed": ComponentConfig(),
            "selectable": ComponentConfig(module="chosen"),
        }
    )
    model = object()

    assert fixed.build(model, context) == ["fixed constraint"]
    assert selectable.build(model, context) == ["selected constraint"]
    assert calls == [
        ("fixed", model, context),
        ("selected", model, context),
    ]


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
