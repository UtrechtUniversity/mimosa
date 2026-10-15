"""Variable metadata collection and shared documentation model construction."""

import importlib
from types import SimpleNamespace

import pytest
from pyomo.environ import ConcreteModel, Constraint, Param, Set, Var, units

from docs.scripts import variable_docs


def test_collects_scalar_time_and_regional_metadata_without_values():
    model = ConcreteModel()
    model.t = Set(initialize=[0, 1])
    model.regions = Set(initialize=["A", "B"])
    model.scalar = Var(doc="One constant", units=units.m)
    model.time = Var(model.t, doc="An annual flow", units=units.kg / units.a)
    model.regional = Var(model.t, model.regions, doc="Regional quantity")
    model.region_only = Var(model.regions)
    model.reversed = Var(model.regions, model.t)

    catalogue = variable_docs.collect_variables(model, context="example")
    variables = {variable.name: variable for variable in catalogue}

    assert [variable.name for variable in catalogue] == sorted(variables)
    assert variables["scalar"].description == "One constant"
    assert variables["scalar"].unit == "m"
    assert variables["scalar"].dimensions == ()
    assert variables["time"].unit == "kg/yr"
    assert variables["time"].dimensions == ("t",)
    assert variables["regional"].dimensions == ("t", "regions")
    assert variables["region_only"].dimensions == ("regions",)
    assert variables["reversed"].dimensions == ("regions", "t")
    assert all(variable.context == "example" for variable in catalogue)
    assert all(
        value.value is None
        for var in model.component_objects(Var)
        for value in var.values()
    )


def test_preserves_missing_docs_and_distinguishes_undeclared_units():
    model = ConcreteModel()
    model.missing = Var()
    model.blank = Var(doc=" ")
    model.ratio = Var(doc="An explicit ratio", units=units.dimensionless)

    variables = {
        variable.name: variable
        for variable in variable_docs.collect_variables(model, context="default")
    }

    assert variables["missing"].description is None
    assert variables["blank"].description == " "
    assert variables["missing"].has_declared_units is False
    assert variables["ratio"].has_declared_units is True
    assert variables["ratio"].unit == "dimensionless"


def test_collects_only_public_variables_and_snapshots_the_metadata():
    model = ConcreteModel()
    model.variable = Var(doc="Original description")
    model._internal = Var()
    model.parameter = Param(initialize=0)

    catalogue = variable_docs.collect_variables(model, context="default")
    model.variable.doc = "Changed description"

    assert len(catalogue) == 1
    assert catalogue[0].name == "variable"
    assert catalogue[0].description == "Original description"


@pytest.fixture
def documentation_model(monkeypatch):
    variable_docs.get_documentation_context.cache_clear()
    model = ConcreteModel()
    model.variable = Var(doc="Test variable", units=units.m)
    model.alpha = Param(initialize=0.3, doc="::economics.GDP.alpha")
    model.example_constraint = Constraint(
        expr=model.variable >= 0, doc="Test constraint documentation"
    )
    params = {"example": "configuration"}
    parser_tree = {
        "economics": {
            "GDP": {"alpha": SimpleNamespace(to_string=lambda: "Alpha description")}
        }
    }
    calls = []

    def check_params(overrides, return_parser_tree):
        assert overrides == {}
        assert return_parser_tree is True
        return params, parser_tree

    def construct_model(supplied_params, *, prerun):
        calls.append((supplied_params, prerun))
        return SimpleNamespace(concrete_model=model)

    monkeypatch.setattr(variable_docs, "check_params", check_params)
    monkeypatch.setattr(variable_docs, "MIMOSA", construct_model)
    yield SimpleNamespace(
        model=model, params=params, parser_tree=parser_tree, calls=calls
    )
    variable_docs.get_documentation_context.cache_clear()


def test_provider_reuses_model_and_catalogue_without_prerun(documentation_model):
    first = variable_docs.get_documentation_context()
    second = variable_docs.get_documentation_context()

    assert first is second
    assert first.model is documentation_model.model
    assert first.parser_tree is documentation_model.parser_tree
    assert first.variables[0].name == "variable"
    assert first.variables[0].context == "default"
    assert documentation_model.calls == [(documentation_model.params, False)]


def test_hooks_and_macros_share_lazy_provider(documentation_model):
    hooks = importlib.reload(importlib.import_module("docs.scripts.mkdocs_hooks"))
    macros = importlib.reload(importlib.import_module("docs.scripts.mkdocs_macros"))
    assert documentation_model.calls == []
    handler = SimpleNamespace(update_env=lambda: None)
    env = SimpleNamespace(
        variables={},
        conf={
            "plugins": {
                "mkdocstrings": SimpleNamespace(get_handler=lambda name: handler)
            }
        },
    )

    macros.define_env(env)
    html = hooks.on_page_content("param::alpha")

    assert env.variables["example_constraint"] == "Test constraint documentation"
    assert "Alpha description" in html
    assert "param::alpha" not in html
    assert documentation_model.calls == [(documentation_model.params, False)]


@pytest.mark.parametrize("event", ["on_post_build", "on_build_error"])
def test_build_completion_or_error_clears_shared_model(documentation_model, event):
    hooks = importlib.import_module("docs.scripts.mkdocs_hooks")
    first = variable_docs.get_documentation_context()

    getattr(hooks, event)()
    second = variable_docs.get_documentation_context()

    assert second is not first
    assert len(documentation_model.calls) == 2
