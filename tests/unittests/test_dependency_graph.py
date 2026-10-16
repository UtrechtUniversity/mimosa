"""The graph export keeps variable roles and both dependency types."""

from xml.etree import ElementTree
import json
from pathlib import Path
from types import SimpleNamespace

import networkx as nx
import pytest

from docs.scripts.generate_dependency_graph import build_graph, write_graph
from docs.scripts.variable_docs import DOCUMENTATION_CONFIGS
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


def test_exported_graphs_cover_documentation_contexts_and_match_the_manifest():
    directory = Path(__file__).resolve().parents[2] / "docs/assets/dependency-graphs"
    manifest = json.loads((directory / "index.json").read_text())
    assert manifest["default_context"] == "coacch"
    assert set(manifest["contexts"]) == set(DOCUMENTATION_CONFIGS)
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    for context, entry in manifest["contexts"].items():
        root = ElementTree.parse(directory / entry["source"]).getroot()
        nodes = [group for group in root.findall(".//svg:g", namespace) if "node" in group.get("class", "").split()]
        assert sorted(node.find("svg:title", namespace).text for node in nodes) == entry["variables"]
        assert entry["label"] != context
        for node in nodes:
            link = node.find(".//svg:a", namespace)
            assert f"graph_context={context}" in link.attrib["{http://www.w3.org/1999/xlink}href"]
