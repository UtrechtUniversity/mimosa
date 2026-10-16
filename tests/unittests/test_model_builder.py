from types import SimpleNamespace

import pytest

from mimosa import model_builder
from mimosa.common import ConcreteModel, Objective
from mimosa.components import (
    damages,
    effortsharing,
    emissiontrade,
    financialtransfer,
    objective,
    welfare,
)


MODULE_GROUPS = [
    (damages, "damage", damages.DAMAGE_MODULES),
    (emissiontrade, "emissiontrade", emissiontrade.EMISSIONTRADE_MODULES),
    (financialtransfer, "financialtransfer", financialtransfer.FINANCIALTRANSFER_MODULES),
    (effortsharing, "effortsharing", effortsharing.EFFORTSHARING_MODULES),
    (welfare, "welfare", welfare.WELFARE_MODULES),
    (objective, "objective", objective.OBJECTIVE_MODULES),
]


@pytest.mark.parametrize(
    "package,config_name,registry,selection",
    [
        (package, config_name, registry, selection)
        for package, config_name, registry in MODULE_GROUPS
        for selection in registry
    ],
)
def test_package_builds_selected_module(monkeypatch, package, config_name, registry, selection):
    model = object()
    config_calls = []
    module_calls = []
    result = (object(), [object()]) if package is objective else [object()]

    def config_value(path):
        config_calls.append(path)
        return selection

    inputs = SimpleNamespace(config_value=config_value)

    def get_constraints(m, supplied_inputs):
        module_calls.append((m, supplied_inputs))
        return result

    monkeypatch.setitem(registry, selection, get_constraints)

    assert package.get_constraints(model, inputs) is result
    assert config_calls == [f"model structure.{config_name} module"]
    assert module_calls == [(model, inputs)]


@pytest.mark.parametrize("package,config_name,registry", MODULE_GROUPS)
def test_package_reports_unknown_module(package, config_name, registry):
    inputs = SimpleNamespace(config_value=lambda _path: "unknown")

    with pytest.raises(NotImplementedError) as error:
        package.get_constraints(object(), inputs)

    assert str(error.value) == (
        f"Module `unknown` not implemented. Available modules: {list(registry)}"
    )


def test_builder_constructs_components_in_order_and_adds_objective(monkeypatch):
    """Declare every component before attaching constraints or the objective."""
    model = ConcreteModel()
    inputs = object()
    calls = []
    model_objective = Objective(expr=0)
    constraint = SimpleNamespace(
        name="objective_constraint",
        to_pyomo_constraint=lambda m: calls.append(("convert", m)),
    )
    monkeypatch.setattr(model_builder, "create_base_model", lambda supplied: model)
    component_names = [
        "emissions", "sealevelrise", "damages", "mitigation", "emissiontrade",
        "financialtransfer", "effortsharing", "cobbdouglas", "welfare",
    ]

    def record_component(name):
        def get_constraints(m, supplied_inputs):
            calls.append((name, m, supplied_inputs))
            return []
        return get_constraints

    for name in component_names:
        monkeypatch.setattr(
            getattr(model_builder, name), "get_constraints", record_component(name)
        )

    def get_objective(m, supplied_inputs):
        calls.append(("objective", m, supplied_inputs))
        return model_objective, [constraint]

    monkeypatch.setattr(objective, "get_constraints", get_objective)
    monkeypatch.setattr(
        model_builder, "add_constraint",
        lambda m, pyomo_constraint, name: calls.append(("attach", m, name)),
    )

    built_model, equations = model_builder.create_model(inputs)

    assert built_model is model
    assert model.objective is model_objective
    assert equations == []
    assert calls == [
        *((name, model, inputs) for name in component_names + ["objective"]),
        ("convert", model),
        ("attach", model, "objective_constraint"),
    ]
