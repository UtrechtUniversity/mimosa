"""Baseline plots use initialized model values and the documented time window."""

import json
import pytest
from pyomo.environ import ConcreteModel, Param, Set, value

from docs.scripts import mkdocs_hooks, time_regional_parameter_docs as plots
from docs.scripts.variable_docs import get_documentation_context
from mimosa.common.pyomo_utils import get_unit


def test_default_assets_include_all_regions_and_reuse_the_documentation_model(monkeypatch):
    context = get_documentation_context()
    calls = []

    def cached_context():
        calls.append(True)
        return context

    monkeypatch.setattr(plots, "get_documentation_context", cached_context)
    plots.get_time_regional_parameter_assets.cache_clear()
    try:
        assets = plots.get_time_regional_parameter_assets()
        assert plots.get_time_regional_parameter_assets() is assets
        assert calls == [True]
        assert len(assets) == 3
        model = context.model
        assert len(model.regions) == 26
        assert context.params["SSP"] == "SSP2"
        expected_years = [2025, 2030, 2035, 2040, 2045, 2050, 2060, 2070, 2080, 2090, 2100]
        time_by_year = {value(model.year(t)): t for t in model.t}
        for name, _, _ in plots.BASELINE_PARAMETERS:
            plot = json.loads(assets[f"{plots.PLOT_DIRECTORY}/{name}.json"])
            parameter = getattr(model, name)
            assert plot["layout"]["yaxis"]["title"] == get_unit(parameter)
            assert [trace["name"] for trace in plot["data"]] == list(model.regions)
            assert len({trace["line"]["color"] for trace in plot["data"]}) == 26
            for trace in plot["data"]:
                assert trace["x"] == expected_years
                assert trace["y"] == pytest.approx([
                    value(parameter[time_by_year[year], trace["name"]])
                    for year in expected_years
                ])
    finally:
        plots.get_time_regional_parameter_assets.cache_clear()


def test_plot_preserves_irregular_grid_and_clips_both_ends():
    model = ConcreteModel()
    model.t = Set(initialize=range(5))
    model.regions = Set(initialize=["USA", "CAN"], ordered=True)
    years = [2020, 2025, 2032, 2100, 2110]
    model.year = lambda t: years[t]
    model.population = Param(
        model.t, model.regions,
        initialize=lambda m, t, r: t + (10 if r == "USA" else 20),
    )

    data = plots.create_parameter_plot(model, "population")["data"]
    assert [(trace["name"], trace["x"], trace["y"]) for trace in data] == [
        ("USA", [2025, 2032, 2100], [11, 12, 13]),
        ("CAN", [2025, 2032, 2100], [21, 22, 23]),
    ]


def test_reference_hook_is_lazy_and_labels_the_actual_sources(monkeypatch):
    context = get_documentation_context()
    calls = []

    def cached_context():
        calls.append(True)
        return context

    monkeypatch.setattr(mkdocs_hooks, "get_documentation_context", cached_context)
    assert mkdocs_hooks.on_page_markdown("Ordinary page") == "Ordinary page"
    assert calls == []
    result = mkdocs_hooks.on_page_markdown(plots.TIME_REGIONAL_REFERENCE_MARKER)
    assert calls == [True]
    assert plots.TIME_REGIONAL_REFERENCE_MARKER not in result
    assert "Scenario: SSP2-Baseline" in result
    assert "{SSP}" not in result
    assert context.params["input"]["variables"]["population"]["scenario"] == "{SSP}-Baseline"
    for name, source_name, _ in plots.BASELINE_PARAMETERS:
        assert f'??? parameter "{name}"' in result
        assert f'id="timeandregional.{name}"' in result
        assert f'"file_path": "{plots.PLOT_DIRECTORY}/{name}.json"' in result
        source = context.params["input"]["variables"][source_name]
        assert f"Source: {source['model']}, {source['variable']}" in result
