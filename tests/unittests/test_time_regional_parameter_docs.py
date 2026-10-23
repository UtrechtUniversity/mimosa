"""Discover initialized parameter series and render them without extra models."""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from pyomo.environ import ConcreteModel, Param, Set, Var, units, value

from docs.scripts import mkdocs_hooks, time_regional_parameter_docs as plots
from docs.scripts.variable_docs import get_documentation_context
from mimosa.common import Param as MimosaParam, SourcedValue
from mimosa.common.pyomo_utils import get_unit


@pytest.fixture(autouse=True)
def clear_plot_cache():
    plots.clear_time_regional_parameter_cache()
    yield
    plots.clear_time_regional_parameter_cache()


def example_model():
    model = ConcreteModel()
    model.t = Set(initialize=range(5))
    model.regions = Set(initialize=["USA", "CAN"], ordered=True)
    years = [2020, 2025, 2032, 2100, 2110]
    model.year = lambda t: years[t]
    model.new_parameter = Param(
        model.t, model.regions,
        initialize=lambda m, t, r: t + (10 if r == "USA" else 20),
        doc="A newly declared parameter.",
    )
    return model


def test_discovery_filters_by_type_and_dimensions_and_preserves_grid():
    model = example_model()
    model.reverse = Param(
        model.regions, model.t, initialize=lambda m, r, t: 10 * t,
    )
    model.scalar = Param(initialize=3)
    model.time_only = Param(model.t, initialize=2)
    model.region_only = Param(model.regions, initialize=4)
    model._private = Param(model.t, model.regions, initialize=0)
    model.variable = Var(model.t, model.regions)

    entries = plots.collect_time_regional_parameters(model)
    assert [entry.name for entry in entries] == ["new_parameter", "reverse"]
    assert entries[0].description == "A newly declared parameter."
    assert entries[0].years == (2025, 2032, 2100)
    assert entries[0].regions == ("USA", "CAN")
    assert entries[0].values == ((11, 12, 13), (21, 22, 23))
    assert entries[1].values == ((10, 20, 30), (10, 20, 30))
    data = plots.create_parameter_plot(entries[0])["data"]
    assert [(trace["name"], trace["x"], trace["y"]) for trace in data] == [
        ("USA", (2025, 2032, 2100), (11, 12, 13)),
        ("CAN", (2025, 2032, 2100), (21, 22, 23)),
    ]


def test_zero_and_uninitialized_parameters_are_omitted_but_partial_values_remain():
    model = example_model()
    model.empty = Param(model.t, model.regions, mutable=True)
    model.partial = Param(
        model.t, model.regions, mutable=True, initialize={(1, "USA"): 7},
    )
    # An explicitly accessed but uninitialized entry must also remain missing.
    model.partial[2, "USA"]
    model.zero = Param(model.t, model.regions, default=0)
    model.partial_zero = Param(
        model.t, model.regions, mutable=True, initialize={(1, "USA"): 0},
    )
    model.small = Param(model.t, model.regions, initialize=1e-16)
    model.negative = Param(model.t, model.regions, initialize=-1)
    entries = {entry.name: entry for entry in plots.collect_time_regional_parameters(model)}

    assert "empty" not in entries
    assert "zero" not in entries
    assert "partial_zero" not in entries
    assert len(model.empty) == 0
    assert entries["partial"].values == ((7, None, None), (None, None, None))
    assert len(model.partial) == 2
    assert entries["small"].values == ((1e-16,) * 3,) * 2
    assert entries["negative"].values == ((-1,) * 3,) * 2
    plot = json.loads(json.dumps(plots.create_parameter_plot(entries["partial"]), allow_nan=False))
    assert plot["data"][0]["y"] == [7, None, None]
    assert "connectgaps" not in plot["data"][0]


def test_zero_substitute_does_not_hide_a_nonzero_variant_in_another_context(monkeypatch):
    zero = example_model()
    del zero.new_parameter
    zero.new_parameter = Param(zero.t, zero.regions, initialize=0)
    contexts = {
        "zero": SimpleNamespace(model=zero),
        "nonzero": SimpleNamespace(model=example_model()),
    }
    monkeypatch.setattr(plots.variable_docs, "DOCUMENTATION_CONFIGS", contexts)
    monkeypatch.setattr(plots.variable_docs, "get_documentation_context", contexts.__getitem__)

    entry, = plots.get_time_regional_parameter_catalogue()
    assert entry.name == "new_parameter"
    assert entry.contexts == ("nonzero",)
    assert entry.values == ((11, 12, 13), (21, 22, 23))


@pytest.mark.parametrize("difference", ["values", "description", "source_key", "unit"])
def test_catalogue_merges_identical_entries_but_preserves_variants(monkeypatch, difference):
    first = example_model()
    second = example_model()
    if difference == "values":
        second.new_parameter = Param(second.t, second.regions, initialize=99)
    elif difference == "description":
        second.new_parameter.doc = "Another definition."
    elif difference == "source_key":
        second.new_parameter.source_key = "timeandregional::another_input"
    else:
        second.new_parameter = Param(
            second.t, second.regions,
            initialize=lambda m, t, r: t + (10 if r == "USA" else 20),
            doc=first.new_parameter.doc, units=units.kg,
        )
    contexts = {
        "first": SimpleNamespace(model=first),
        "same": SimpleNamespace(model=first),
        "different": SimpleNamespace(model=second),
    }
    monkeypatch.setattr(plots.variable_docs, "DOCUMENTATION_CONFIGS", contexts)
    monkeypatch.setattr(plots.variable_docs, "get_documentation_context", contexts.__getitem__)
    catalogue = plots.get_time_regional_parameter_catalogue()
    assert plots.get_time_regional_parameter_catalogue() is catalogue
    assert len(catalogue) == 2
    assert catalogue[0].contexts == ("first", "same")
    assert catalogue[1].contexts == ("different",)


def test_default_assets_cover_all_contexts_and_reuse_cached_models(monkeypatch):
    calls = []

    def cached_context(name="default"):
        calls.append(name)
        return get_documentation_context(name)

    monkeypatch.setattr(plots.variable_docs, "get_documentation_context", cached_context)
    catalogue = plots.get_time_regional_parameter_catalogue()
    assert calls == list(plots.variable_docs.DOCUMENTATION_CONFIGS)
    # Every entry comes from an existing cached model, never a simulation.
    assert {entry.name for entry in catalogue} >= {
        "population", "baseline_GDP", "ssp_baseline_emissions", "TFP",
        "percapconv_share", "effortsharing_ecpc_historical_debt",
    }
    omitted = {
        "adaptation_costs", "adaptation_costs_abs", "financial_transfer",
        "financial_transfer_abs", "emission_reduction_trading_balance",
        "mitigation_cost_trading_balance", "non_market_damage_costs_abs",
        "nopolicy_damage_costs",
    }
    assert not omitted.intersection(entry.name for entry in catalogue)
    assets = plots.get_time_regional_parameter_assets()
    call_count = len(calls)
    assert plots.get_time_regional_parameter_assets() is assets
    assert plots.get_time_regional_parameter_catalogue() is catalogue
    assert len(calls) == call_count
    assert len(assets) == len(catalogue)
    for name in omitted:
        assert f"{plots.PLOT_DIRECTORY}/{name}.json" not in assets

    for entry in catalogue:
        plot = json.loads(assets[f"{plots.PLOT_DIRECTORY}/{entry.name}.json"])
        assert plot["layout"]["yaxis"]["title"] == entry.unit
        assert [trace["name"] for trace in plot["data"]] == list(entry.regions)
        assert len({trace["line"]["color"] for trace in plot["data"]}) == 26
        assert all(trace["x"] == list(entry.years) for trace in plot["data"])
        assert [trace["y"] for trace in plot["data"]] == [list(series) for series in entry.values]
        assert "updatemenus" not in plot["layout"]
        context = get_documentation_context(entry.contexts[0])
        assert context.params["SSP"] == "SSP2"
        parameter = getattr(context.model, entry.name)
        assert plot["layout"]["yaxis"]["title"] == get_unit(parameter)
        assert entry.years == (2025, 2030, 2035, 2040, 2045, 2050, 2060, 2070, 2080, 2090, 2100)
        time_by_year = {value(context.model.year(t)): t for t in context.model.t}
        for trace in plot["data"]:
            assert trace["y"] == pytest.approx([
                value(parameter[time_by_year[year], trace["name"]])
                for year in trace["x"]
            ])


def test_reference_hook_is_lazy_and_omits_zero_and_uninitialized_parameters(monkeypatch):
    calls = []

    def render_reference():
        calls.append(True)
        return "Parameter cards"

    with monkeypatch.context() as patch:
        patch.setattr(mkdocs_hooks, "render_time_regional_parameter_reference", render_reference)
        assert mkdocs_hooks.on_page_markdown("Ordinary page") == "Ordinary page"
        assert calls == []
        assert mkdocs_hooks.on_page_markdown(plots.TIME_REGIONAL_REFERENCE_MARKER) == "Parameter cards"
        assert calls == [True]

    context = get_documentation_context()
    original_params = deepcopy(context.params)
    result = plots.render_time_regional_parameter_reference()
    assert plots.TIME_REGIONAL_REFERENCE_MARKER not in result
    assert "Scenario: SSP2" in result
    assert "Scenarios:" not in result
    assert "{SSP}" not in result
    assert context.params == original_params
    assert '??? parameter "TFP"' in result
    assert '??? parameter "adaptation_costs"' not in result
    assert '??? parameter "nopolicy_damage_costs"' not in result
    assert f'"file_path": "{plots.PLOT_DIRECTORY}/nopolicy_damage_costs.json"' not in result
    for entry in plots.get_time_regional_parameter_catalogue():
        assert f'??? parameter "{entry.name}"' in result
        assert f'id="timeandregional.{entry.name}"' in result
        assert f'"file_path": "{plots.PLOT_DIRECTORY}/{entry.name}.json"' in result
        if entry.source_name:
            source = context.params["input"]["variables"][entry.source_name]
            assert f"Source: {source['model']}, {source['variable']}" in result
    debt = result.split('??? parameter "effortsharing_ecpc_historical_debt"')[1].split('??? parameter')[0]
    assert "Available when:" in debt
    assert "params['model structure']['effortsharing module'] = 'equal_cumulative_per_cap'" in debt
    assert "effortsharing_equal_cumulative_per_cap" not in debt


@pytest.mark.parametrize("description", [None, "A custom input description."])
def test_reference_uses_doc_without_losing_source_metadata(monkeypatch, description):
    default = get_documentation_context()
    model = example_model()
    model.population = MimosaParam(
        model.t, model.regions,
        initialize=SourcedValue(
            {(t, r): 1.0 for t in model.t for r in model.regions},
            "timeandregional::population",
        ),
        doc=description,
    )
    context = SimpleNamespace(
        model=model, params=default.params, parser_tree=default.parser_tree,
    )
    monkeypatch.setattr(plots.variable_docs, "DOCUMENTATION_CONFIGS", {"coacch": {}})
    monkeypatch.setattr(plots.variable_docs, "get_documentation_context", lambda name: context)

    result = plots.render_time_regional_parameter_reference()
    population = next(
        entry for entry in plots.get_time_regional_parameter_catalogue()
        if entry.name == "population"
    )
    assert population.description == description
    assert population.source_key == "timeandregional::population"
    assert population.source_name == "population"
    fallback = default.parser_tree["input"]["variables"]["population"].descr
    assert (description or fallback) in result
    assert "Source: IMAGE 3.4, Population" in result
    assert '"file_path": "assets/parameter-plots/population.json"' in result


def test_variants_have_distinct_assets_but_one_card_and_anchor(monkeypatch):
    default = get_documentation_context()
    first = example_model()
    second = example_model()
    second.new_parameter = Param(second.t, second.regions, initialize=99)
    contexts = {}
    for name, model, module in [("one", first, "COACCH"), ("two", second, "ACCREU")]:
        params = deepcopy(default.params)
        params["model structure"]["damage module"] = module
        contexts[name] = SimpleNamespace(model=model, params=params)
    monkeypatch.setattr(plots.variable_docs, "DOCUMENTATION_CONFIGS", contexts)
    monkeypatch.setattr(plots.variable_docs, "get_documentation_context", contexts.__getitem__)

    assets = plots.get_time_regional_parameter_assets()
    assert len(assets) == 2
    first_plot = json.loads(assets[f"{plots.PLOT_DIRECTORY}/new_parameter.json"])
    second_plot = json.loads(assets[f"{plots.PLOT_DIRECTORY}/new_parameter-2.json"])
    assert first_plot["data"][0]["y"] == [11, 12, 13]
    assert second_plot["data"][0]["y"] == [99, 99, 99]
    markdown = plots.render_time_regional_parameter_reference()
    assert markdown.count('??? parameter "new_parameter"') == 1
    assert markdown.count('id="timeandregional.new_parameter"') == 1
    assert 'new_parameter-2.json' in markdown
    assert "'damage module'] = 'COACCH'" in markdown
    assert "'damage module'] = 'ACCREU'" in markdown


@pytest.mark.parametrize("lifecycle_hook", [mkdocs_hooks.on_startup, mkdocs_hooks.on_shutdown])
def test_command_lifecycle_clears_series_and_asset_caches(lifecycle_hook):
    plots.get_time_regional_parameter_catalogue()
    plots.get_time_regional_parameter_assets()
    lifecycle_hook()
    assert plots.get_time_regional_parameter_catalogue.cache_info().currsize == 0
    assert plots.get_time_regional_parameter_assets.cache_info().currsize == 0
