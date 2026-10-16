"""Export one real dependency graph for the interactive documentation prototype.

Run with ``python -m docs.scripts.generate_dependency_demo`` in the accreu
environment. This constructs equations but never simulates or solves the model.
"""

from pathlib import Path
from urllib.parse import urlencode

from networkx.drawing.nx_agraph import to_agraph

from mimosa import MIMOSA, load_params
from mimosa.common import Var, add_constraint
from mimosa.components.after_initialisation import avoided_damages


def write_graph(graph, output):
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
        node.attr.update(
            label=label,
            id=f"demo-node-{name}",
            URL="?" + urlencode({"demo_variable": name}) + "#dependency-graph-demo",
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
    write_graph(graph, output)
    previous = sum(data["type"] == "prev_time_dependency" for _, _, data in graph.edges(data=True))
    print(
        f"Exported {len(graph)} variables, {graph.number_of_edges() - previous} "
        f"current-time and {previous} previous-time dependencies to {output}"
    )


if __name__ == "__main__":
    main()
