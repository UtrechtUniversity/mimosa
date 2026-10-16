"""The graph export keeps variables and current-time links without simulation."""

from xml.etree import ElementTree

import networkx as nx
import pytest

from docs.scripts.generate_dependency_demo import write_graph


def test_export_keeps_isolated_variables_and_excludes_previous_time_edges(tmp_path):
    pytest.importorskip("pygraphviz")
    graph = nx.DiGraph()
    graph.add_node("input", has_equation=False)
    graph.add_node("output", has_equation=True)
    graph.add_node("isolated", has_equation=True)
    graph.add_edge("input", "output", type="dependency")
    graph.add_edge("output", "input", type="prev_time_dependency")
    output = tmp_path / "graph.svg"

    current = write_graph(graph, output)

    assert set(current) == {"input", "output", "isolated"}
    assert set(current.edges) == {("input", "output")}
    root = ElementTree.parse(output).getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}
    nodes = root.findall('.//svg:g[@class="node"]', namespace)
    edges = root.findall('.//svg:g[@class="edge"]', namespace)
    assert len(nodes) == 3
    assert len(edges) == 1
    assert edges[0].find("svg:title", namespace).text == "input->output"
    for node in nodes:
        name = node.find("svg:title", namespace).text
        link = node.find(".//svg:a", namespace)
        assert link.attrib["{http://www.w3.org/1999/xlink}href"] == (
            f"?demo_variable={name}#dependency-graph-demo"
        )
