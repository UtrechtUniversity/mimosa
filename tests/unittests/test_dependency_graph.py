"""The graph export keeps variable roles and both dependency types."""

from xml.etree import ElementTree
from types import SimpleNamespace

import networkx as nx
import pytest

from docs.scripts.generate_dependency_graph import (
    build_graph, write_graph, configuration_example, context_graph,
)
from mimosa.common import ConcreteModel, Set, Var, GlobalEquation, add_constraint


def test_export_keeps_roles_isolated_variables_and_previous_time_edges(tmp_path):
    pytest.importorskip("pygraphviz")
    graph = nx.DiGraph()
    graph.add_node("input", has_equation=False)
    graph.add_node("output", has_equation=True)
    graph.add_node("isolated", has_equation=True)
    graph.add_edge("input", "output", type="dependency")
    graph.add_edge("output", "input", type="prev_time_dependency")
    output = tmp_path / "graph.svg"

    exported = write_graph(graph, output)

    assert set(exported) == {"input", "output", "isolated"}
    assert set(exported.edges) == {("input", "output"), ("output", "input")}
    root = ElementTree.parse(output).getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    groups = root.findall(".//svg:g", namespace)
    nodes = [group for group in groups if "node" in group.get("class", "").split()]
    edges = [group for group in groups if "edge" in group.get("class", "").split()]
    assert len(nodes) == 3
    assert len(edges) == 2
    types = {
        edge.find("svg:title", namespace).text: edge.get("class").split()
        for edge in edges
    }
    assert "current-time" in types["input->output"]
    assert "previous-time" in types["output->input"]
    for node in nodes:
        name = node.find("svg:title", namespace).text
        assert ("control" if name == "input" else "calculated") in node.get("class").split()
        link = node.find(".//svg:a", namespace)
        assert link.attrib["{http://www.w3.org/1999/xlink}href"] == (
            f"?graph_variable={name}#dependency-graph"
        )


def test_graph_analysis_supports_cycles_and_previous_time_without_running_model():
    m = ConcreteModel()
    m.t = Set(initialize=[0, 1])
    m.a = Var(m.t)
    m.b = Var(m.t)
    m.control = Var(m.t)
    equations = [
        GlobalEquation(m.a, lambda m, t: m.b[t] + (m.a[t - 1] if t else 0)),
        GlobalEquation(m.b, lambda m, t: m.a[t]),
    ]
    for equation in equations:
        add_constraint(m, equation.to_pyomo_constraint(m), equation.name)
    graph = build_graph(SimpleNamespace(concrete_model=m, equations=equations))

    assert set(graph) == {"a", "b", "control"}
    assert graph.nodes["a"]["has_equation"] is True
    assert graph.nodes["control"]["has_equation"] is False
    assert graph.edges["a", "a"]["type"] == "prev_time_dependency"
    assert graph.edges["a", "b"]["type"] == "dependency"
    assert graph.edges["b", "a"]["type"] == "dependency"


def test_configuration_example_only_sets_overrides_and_is_executable():
    from html import unescape
    import re
    from copy import deepcopy
    from mimosa.common.config.parseconfig import check_params
    from docs.scripts.variable_docs import DOCUMENTATION_CONFIGS

    defaults = check_params({})
    html = configuration_example(DOCUMENTATION_CONFIGS["accreu_sectoral"], defaults)
    code = unescape(re.sub(r"<[^>]+>", "", html)).strip()
    assert code.splitlines() == [
        "params = load_params()",
        "params['model structure']['damage module'] = 'ACCREU'",
        "params['economics']['damages']['accreu']['adaptation'] = 'sectoral'",
        "model = MIMOSA(params)",
    ]
    # Every example must reproduce the corresponding fully parsed configuration.
    for settings in DOCUMENTATION_CONFIGS.values():
        html = configuration_example(settings, defaults)
        code = unescape(re.sub(r"<[^>]+>", "", html))
        namespace = {"load_params": lambda: deepcopy(defaults), "MIMOSA": lambda p: p}
        exec(code, namespace)
        assert namespace["model"] == check_params(settings)


def test_failed_graph_analysis_removes_temporary_baseline_constraints(monkeypatch):
    from docs.scripts import generate_dependency_graph

    m = ConcreteModel()
    m.t = Set(initialize=[0, 1])
    m.a = Var(m.t)
    m.b = Var(m.t)
    equation = GlobalEquation(m.a, lambda m, t: m.b[t])
    context = SimpleNamespace(model=m, equations=(), baseline_equations=(equation,))

    def fail_analysis(model):
        assert hasattr(m, "constraint_a")
        raise ValueError("Failed graph analysis")

    monkeypatch.setattr(generate_dependency_graph, "build_graph", fail_analysis)
    with pytest.raises(ValueError, match="Failed graph analysis"):
        context_graph(context)
    assert not hasattr(m, "constraint_a")
