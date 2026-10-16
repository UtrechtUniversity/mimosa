"""Export one real dependency graph for the interactive documentation prototype.

Run with ``python -m docs.scripts.generate_dependency_demo`` in the accreu
environment. This constructs equations but never simulates or solves the model.
"""

from pathlib import Path
from urllib.parse import urlencode

import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

from mimosa import MIMOSA, load_params
from mimosa.common import Var, add_constraint
from mimosa.components.after_initialisation import avoided_damages


def write_graph(graph, output):
    """Lay out the same dependency data as the plot, omitting previous-time edges."""
    current = nx.DiGraph()
    current.add_nodes_from(graph.nodes(data=True))
    current.add_edges_from(
        (source, target)
        for source, target, data in graph.edges(data=True)
        if data["type"] == "dependency"
    )
    drawing = to_agraph(current)
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
        node.attr.update(
            label=label,
            id=f"demo-node-{name}",
            URL="?" + urlencode({"demo_variable": name}) + "#dependency-graph-demo",
            tooltip=name,
            fillcolor="#89a041" if graph.nodes[name].get("has_equation") else "#ed6a2f",
        )

    drawing.draw(str(output), format="svg", prog="dot")
    return current


def main():
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    params["economics"]["damages"]["accreu"]["adaptation"] = "sectoral"
    params["economics"]["damages"]["accreu"]["adaptation_determination"] = "solver_control"
    model = MIMOSA(params, prerun=False)

    # Include avoided-damage equations symbolically, without running a baseline.
    for equation in avoided_damages.get_constraints(model.concrete_model):
        add_constraint(
            model.concrete_model,
            equation.to_pyomo_constraint(model.concrete_model),
            equation.name,
        )
        model.equations.append(equation)
    model.prepare_simulation()
    graph = model.simulator.equations_graph.copy()

    # The plot omits isolated equations; keep every public variable in this view.
    equations = {equation.name for equation in model.equations}
    for variable in model.concrete_model.component_objects(Var):
        if not variable.name.startswith("_"):
            graph.add_node(variable.name, has_equation=variable.name in equations)

    output = Path(__file__).resolve().parents[1] / "assets" / "dependency-demo.svg"
    current = write_graph(graph, output)
    print(
        f"Exported {len(current)} variables and {current.number_of_edges()} "
        f"current-time dependencies to {output}"
    )


if __name__ == "__main__":
    main()
