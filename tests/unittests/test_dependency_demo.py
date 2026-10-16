"""The graph export keeps variable roles and both dependency types."""

from xml.etree import ElementTree

import networkx as nx
import pytest

from docs.scripts.generate_dependency_demo import write_graph


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
            f"?demo_variable={name}#dependency-graph-demo"
        )
