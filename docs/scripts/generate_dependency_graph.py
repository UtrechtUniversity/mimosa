"""Export context-specific dependency graphs for the documentation viewer.

Run with ``python -m docs.scripts.generate_dependency_graph`` in the accreu
environment. This constructs equations but never simulates or solves the model.
"""

from copy import deepcopy
import json
from pathlib import Path
from urllib.parse import urlencode

import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

from mimosa import MIMOSA
from mimosa.common import Var, add_constraint
from mimosa.components.after_initialisation import avoided_damages
from mimosa.common.config.parseconfig import check_params
from mimosa.core.simulation.helpers import calc_dependencies
from docs.scripts.variable_docs import DOCUMENTATION_CONFIGS


def write_graph(graph, output, context=None):
    """Export variable roles and both edge types, laying out by current time."""
    drawing = to_agraph(graph)
    drawing.graph_attr.update(
        rankdir="LR", nodesep="0.35", ranksep="0.8", bgcolor="transparent"
    )
    drawing.node_attr.update(
        shape="box", style="rounded,filled", fontname="sans-serif",
        fontsize="13", margin="0.14,0.1",
    )
    drawing.edge_attr.update(color="#999", arrowsize="0.7")

    for node in drawing.nodes():
        name = str(node)
        parts = name.split("_")
        middle = (len(parts) + 1) // 2
        label = "_".join(parts[:middle])
        if middle < len(parts):
            label += "\n" + "_".join(parts[middle:])
        query = {"graph_variable": name}
        if context is not None:
            query["graph_context"] = context
        node.attr.update(
            label=label,
            id=f"dependency-node-{name}",
            URL="?" + urlencode(query) + "#dependency-graph",
            tooltip=name,
            fillcolor="#89a041" if graph.nodes[name].get("has_equation") else "#ed6a2f",
            **{"class": "calculated" if graph.nodes[name].get("has_equation") else "control"},
        )

    for source, target, data in graph.edges(data=True):
        previous_time = data["type"] == "prev_time_dependency"
        edge = drawing.get_edge(source, target)
        edge.attr.update(
            constraint="false" if previous_time else "true",
            style="dashed" if previous_time else "solid",
            color="#cccccc" if previous_time else "#999999",
            **{"class": "previous-time" if previous_time else "current-time"},
        )

    drawing.draw(str(output), format="svg", prog="dot")
    return graph


def build_graph(model):
    """Use the simulator's dependency analysis, including graphs with cycles."""
    equations = {equation.name: equation for equation in model.equations}
    calc_dependencies(equations, model.concrete_model)
    graph = nx.DiGraph()
    for variable in model.concrete_model.component_objects(Var):
        if not variable.name.startswith("_"):
            graph.add_node(variable.name, has_equation=variable.name in equations)
    for name, equation in equations.items():
        for dependencies, kind in (
            (equation.dependencies, "dependency"),
            (equation.prev_time_dependencies, "prev_time_dependency"),
        ):
            for dependency in dependencies:
                if dependency in graph and name in graph:
                    graph.add_edge(dependency, name, type=kind)
    return graph


def configuration_label(config):
    """Describe the actual parameter choices rather than the internal context ID."""
    settings = []
    for key, value in config.items():
        if isinstance(value, dict):
            settings.append(configuration_label(value))
        else:
            settings.append(f"{key.replace('_', ' ')}: {value}")
    return " · ".join(settings)


def export_context(context, output):
    params = check_params(deepcopy(DOCUMENTATION_CONFIGS[context]))
    model = MIMOSA(params, prerun=False)
    # Include avoided-damage equations symbolically, without running a baseline.
    for equation in avoided_damages.get_constraints(model.concrete_model):
        add_constraint(
            model.concrete_model,
            equation.to_pyomo_constraint(model.concrete_model),
            equation.name,
        )
        model.equations.append(equation)
    graph = build_graph(model)
    write_graph(graph, output, context)
    settings = deepcopy(DOCUMENTATION_CONFIGS[context])
    if params["model structure"]["damage module"] == "ACCREU":
        accreu = params["economics"]["damages"]["accreu"]
        if accreu["adaptation"] != "noadaptation":
            settings["economics"]["damages"]["accreu"]["adaptation_determination"] = accreu["adaptation_determination"]
    return {
        "label": configuration_label(settings),
        "source": output.name,
        "variables": sorted(graph),
    }


def main():
    output = Path(__file__).resolve().parents[1] / "assets" / "dependency-graphs"
    output.mkdir(exist_ok=True)
    contexts = {}
    for context in DOCUMENTATION_CONFIGS:
        contexts[context] = export_context(context, output / f"{context}.svg")
        print(f"Exported {context}: {len(contexts[context]['variables'])} variables")
    manifest = {"default_context": "coacch", "contexts": contexts}
    (output / "index.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
