"""Variable metadata collection and shared documentation model construction."""

import importlib
import sys
from types import SimpleNamespace

import pytest
from pyomo.environ import ConcreteModel, Constraint, Param, Set, Var, units

from docs.scripts import variable_docs
from mimosa import MIMOSA
from mimosa.common.config.parseconfig import check_params
from mimosa.components import (
    damages,
    effortsharing,
    emissiontrade,
    financialtransfer,
    objective,
    welfare,
)


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
    variable_docs.clear_documentation_cache()
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
        assert overrides == variable_docs.DOCUMENTATION_CONFIGS["coacch"]
        assert overrides is not variable_docs.DOCUMENTATION_CONFIGS["coacch"]
        assert return_parser_tree is True
        return params, parser_tree

    def construct_model(supplied_params, *, prerun):
        calls.append((supplied_params, prerun))
        return SimpleNamespace(concrete_model=model, equations=())

    monkeypatch.setattr(variable_docs, "check_params", check_params)
    monkeypatch.setattr(variable_docs, "MIMOSA", construct_model)
    monkeypatch.setattr(
        variable_docs.avoided_damages, "get_constraints", lambda model: []
    )
    yield SimpleNamespace(
        model=model, params=params, parser_tree=parser_tree, calls=calls
    )
    variable_docs.clear_documentation_cache()


def test_provider_reuses_model_and_catalogue_without_prerun(documentation_model):
    first = variable_docs.get_documentation_context()
    second = variable_docs.get_documentation_context()

    assert first is second
    assert first.model is documentation_model.model
    assert first.parser_tree is documentation_model.parser_tree
    assert first.variables[0].name == "variable"
    assert first.variables[0].context == "coacch"
    assert variable_docs.get_documentation_context("coacch") is first
    assert documentation_model.calls == [(documentation_model.params, False)]


def test_hooks_import_without_the_optional_mkdocs_package(monkeypatch):
    monkeypatch.setitem(sys.modules, "mkdocs.structure.files", None)
    importlib.reload(importlib.import_module("docs.scripts.mkdocs_hooks"))


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


@pytest.mark.parametrize("event", ["on_startup", "on_shutdown"])
def test_command_lifecycle_clears_shared_model(documentation_model, monkeypatch, event):
    monkeypatch.setattr(
        variable_docs,
        "DOCUMENTATION_CONFIGS",
        {"coacch": variable_docs.DOCUMENTATION_CONFIGS["coacch"]},
    )
    hooks = importlib.import_module("docs.scripts.mkdocs_hooks")
    first = variable_docs.get_documentation_context()
    first_catalogue = variable_docs.get_variable_catalogue()

    getattr(hooks, event)()
    second = variable_docs.get_documentation_context()

    assert second is not first
    assert variable_docs.get_variable_catalogue() is not first_catalogue
    assert len(documentation_model.calls) == 2


@pytest.mark.parametrize(
    "selection,registry",
    [
        ("damage module", damages.DAMAGE_MODULES),
        ("emissiontrade module", emissiontrade.EMISSIONTRADE_MODULES),
        ("financialtransfer module", financialtransfer.FINANCIALTRANSFER_MODULES),
        ("effortsharing module", effortsharing.EFFORTSHARING_MODULES),
        ("welfare module", welfare.WELFARE_MODULES),
        ("objective module", objective.OBJECTIVE_MODULES),
    ],
)
def test_documentation_configs_cover_module_selections(selection, registry):
    selections = {
        check_params(config)["model structure"][selection]
        for config in variable_docs.DOCUMENTATION_CONFIGS.values()
    }

    expected = set(registry)
    if selection == "damage module":
        # These modules reuse variable names already covered by COACCH/ACCREU.
        expected -= {"nodamage", "ACCREU_CGE"}
    elif selection == "emissiontrade module":
        # This module is planned for removal and is intentionally undocumented.
        expected.discard("globalcostpool")
    assert selections <= set(registry)
    assert (
        expected <= selections
    ), f"Missing variable-declaring modules: {expected - selections}"


@pytest.fixture(scope="module")
def documentation_contexts():
    """Construct the real documentation matrix, forbidding runtime workflows."""
    variable_docs.clear_documentation_cache()
    constructions = []

    def forbid_execution(*args, **kwargs):
        pytest.fail("Documentation must not simulate or solve the model")

    def construct_model(params, *, prerun):
        assert prerun is False
        constructions.append(params)
        return MIMOSA(params, prerun=prerun)

    with pytest.MonkeyPatch.context() as patch:
        for method in (
            "prepare_simulation",
            "prerun_simulation",
            "run_nopolicy_baseline",
            "run_simulation",
            "solve",
        ):
            patch.setattr(MIMOSA, method, forbid_execution)
        patch.setattr(variable_docs, "MIMOSA", construct_model)
        try:
            contexts = {
                name: variable_docs.get_documentation_context(name)
                for name in variable_docs.DOCUMENTATION_CONFIGS
            }
            yield contexts, constructions
        finally:
            variable_docs.clear_documentation_cache()


@pytest.mark.parametrize("adaptation", ["noadaptation", "sectoral"])
def test_accreu_contexts_cover_adaptation_declarations(
    documentation_contexts, adaptation
):
    contexts, _ = documentation_contexts
    context = contexts[f"accreu_{adaptation}"]
    names = {variable.name for variable in context.variables}

    for sector in ("slr", "riverine", "labourprod"):
        assert (f"{sector}_damage_costs_gross" in names) == (
            adaptation != "noadaptation"
        )
        assert (f"{sector}_adaptation_costs" in names) == (
            adaptation == "sectoral" or (sector == "slr" and adaptation == "combined")
        )
    assert ("adaptation_costs" in names) == (adaptation != "noadaptation")
    assert ("global_adaptation_costs" in names) == (adaptation != "noadaptation")
    assert ("combined_labprod_riv_damage_costs" in names) == (adaptation == "combined")
    assert ("labourprod_damage_costs_net" in names) == (adaptation != "combined")
    assert ("riverine_damage_costs" in names) == (adaptation != "combined")
    assert context.params["economics"]["damages"]["accreu"]["adaptation"] == adaptation
    if adaptation == "noadaptation":
        assert context.model.adaptation_costs.ctype is Param
    else:
        assert context.model.adaptation_costs.ctype is Var


def test_baseline_dependent_variables_are_declared_without_evaluating_them(
    documentation_contexts,
):
    contexts, _ = documentation_contexts
    for context in contexts.values():
        baseline = {
            variable.name: variable
            for variable in context.variables
            if variable.requires_baseline
        }
        assert set(baseline) == {"avoided_damage_costs", "global_avoided_damage_costs"}
        assert baseline["avoided_damage_costs"].dimensions == ("t", "regions")
        assert baseline["global_avoided_damage_costs"].dimensions == ("t",)
        assert not hasattr(context.model, "constraint_avoided_damage_costs")
        for name in baseline:
            assert all(
                value.value is None for value in getattr(context.model, name).values()
            )


def test_catalogue_and_graphs_preserve_contexts_and_construct_each_model_once(
    documentation_contexts,
):
    contexts, constructions = documentation_contexts
    catalogue = variable_docs.get_variable_catalogue()

    assert variable_docs.get_variable_catalogue() is catalogue
    assert variable_docs.get_documentation_context() is contexts["coacch"]
    assert len(constructions) == len(contexts)
    assert {variable.context for variable in catalogue} == set(contexts)
    assert sum(variable.name == "NPV" for variable in catalogue) == len(contexts)
    assert (
        contexts["objective_globalcosts"].params["model structure"]["objective module"]
        == "globalcosts"
    )
    assert (
        contexts["welfare_inequal_aversion_general"].params["model structure"][
            "welfare module"
        ]
        == "inequal_aversion_general"
    )

    import json
    from xml.etree import ElementTree
    from docs.scripts.generate_dependency_graph import get_dependency_graph_assets

    pytest.importorskip("pygraphviz")
    contexts, constructions = documentation_contexts
    count = len(constructions)
    get_dependency_graph_assets.cache_clear()
    try:
        assets = get_dependency_graph_assets()
        assert get_dependency_graph_assets() is assets
        assert len(constructions) == count == len(variable_docs.DOCUMENTATION_CONFIGS)
        manifest = json.loads(assets["assets/dependency-graphs/index.json"])
        assert set(manifest["contexts"]) == set(contexts)
        namespace = {"svg": "http://www.w3.org/2000/svg"}
        for name, context in contexts.items():
            entry = manifest["contexts"][name]
            root = ElementTree.fromstring(assets[f"assets/dependency-graphs/{entry['source']}"])
            nodes = [g for g in root.findall(".//svg:g", namespace)
                     if "node" in g.get("class", "").split()]
            assert sorted(g.find("svg:title", namespace).text for g in nodes) == entry["variables"]
            assert entry["variables"] == sorted(v.name for v in context.variables)
            assert "load_params" in entry["configuration_html"]
            for equation in context.baseline_equations:
                assert not hasattr(context.model, "constraint_" + equation.name)
    finally:
        get_dependency_graph_assets.cache_clear()


def test_unknown_context_is_rejected_without_building_a_model(documentation_model):
    with pytest.raises(ValueError, match="Unknown documentation context"):
        variable_docs.get_documentation_context("unknown")

    assert documentation_model.calls == []


@pytest.mark.parametrize("name", variable_docs.DOCUMENTATION_CONFIGS)
def test_each_available_configuration_constructs(documentation_contexts, name):
    contexts, _ = documentation_contexts
    assert contexts[name].variables
    assert all(variable.context == name for variable in contexts[name].variables)
