from typing import Union
import re
import networkx as nx

from mimosa.common import (
    ConcreteModel,
    AbstractModel,
    RegionalEquation,
    GlobalEquation,
    Equation,
    Param,
)


def calc_dependencies(equations_dict, m: Union[ConcreteModel, AbstractModel]):
    """
    For each equation in the equations_dict, see what variables the LHS depends on.
    These dependencies are saved to the `dependencies` attribute of each equation.

    This function evaluates the expression of the equation at timestep 1 (not zero, as
    some equations are not defined at timestep 0) and extracts the variable strings used
    in the expression.
    """

    def _extract_variables(expr_str, timestep):
        pattern = f"([a-zA-Z_0-9]+)\\[{timestep}"
        matches = re.findall(pattern, expr_str)
        return matches

    def _filter_out_params(variables):
        return [v for v in variables if not isinstance(getattr(m, v, None), Param)]

    timestep = 1
    for name, eq in equations_dict.items():
        if isinstance(eq, RegionalEquation):
            index = (timestep, "CAN")
        else:
            index = (timestep,)

        expr = str(getattr(m, "constraint_" + name)[index].expr)
        expr_rhs = expr.split("==")[1]
        variables = set(_extract_variables(expr_rhs, timestep))
        # Only keep variables, not params:
        variables = _filter_out_params(variables)

        prev_timestep_dependencies = _filter_out_params(
            set(_extract_variables(expr_rhs, timestep - 1))
        )
        prev_timestep_dependencies = list(
            set(prev_timestep_dependencies) - set(variables)
        )

        # Save the dependencies to the equation:
        eq.dependencies = variables
        eq.prev_time_dependencies = prev_timestep_dependencies


def sort_equations(equations_dict, return_graph=False):
    """
    Sort equations based on their dependencies.
    This function creates a directed graph where each equation is a node,
    and an edge from A to B means that A depends on B.
    It then performs a topological sort to order the equations.
    This way, equations that depend on others will be processed after their dependencies.

    Returns a list of equations sorted in the order they can be evaluated.

    Raises an error if circular dependencies are detected.
    """

    # Create a directed graph
    G = nx.DiGraph()  # Contains only hard dependencies
    G_full = nx.DiGraph()  # Also contains previous time step dependencies

    equations_sorted = []

    # Add edges
    for node, eq in equations_dict.items():
        for dep in eq.dependencies:
            G.add_edge(dep, node)
            G_full.add_edge(dep, node, type="dependency")
        for prev_dep in eq.prev_time_dependencies:
            G_full.add_edge(prev_dep, node, type="prev_time_dependency")

    cycles = list(nx.simple_cycles(G))
    if cycles:
        error_msg = "Circular dependencies found:\n\n"
        for cycle in cycles:
            error_msg += " -> ".join(cycle) + "\n"
        raise CircularDependencyError(error_msg)
    else:
        # Topological sort
        ordered_nodes = list(nx.topological_sort(G))
        for node in ordered_nodes:
            try:
                equations_sorted.append(equations_dict[node])
                G_full.nodes[node]["has_equation"] = True
            except KeyError:
                # print(f"Warning: no equation found for {node}, skipping.")
                G_full.nodes[node]["has_equation"] = False

    if return_graph:
        return equations_sorted, G_full
    return equations_sorted


def plot_dependency_graph(G):

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    try:
        from networkx.drawing.nx_agraph import graphviz_layout
    except ImportError:
        raise ImportError("Please install pygraphviz: pip install pygraphviz")

    def _split_at_middle_underscore(s):
        underscores = [i for i, c in enumerate(s) if c == "_"]
        if not underscores:
            return s  # No underscore
        middle = underscores[len(underscores) // 2]
        return s[:middle] + "\n" + s[middle:]  # omit the underscore itself

    # Build label mapping for nodes
    formatted_labels = {node: _split_at_middle_underscore(node) for node in G.nodes}

    # Create one graph for hard dependencies, used to calculate the layout. The edges for previous time
    # step dependencies will be added later separately.

    G_hard = nx.DiGraph()
    G_hard.add_nodes_from(G.nodes())
    hard_edges = [(u, v) for u, v, d in G.edges(data=True) if d["type"] == "dependency"]
    G_hard.add_edges_from(hard_edges)

    # Use graphviz layout (tree-style, top-down)
    pos = graphviz_layout(
        G_hard,
        prog="dot",
        args="-Grankdir=LR -Gconcentrate=true",
    )

    mimosa_green = "#89a041"
    mimosa_orange = "#ed6a2f"

    node_colors = [
        mimosa_green if G.nodes[node].get("has_equation", False) else mimosa_orange
        for node in G.nodes
    ]

    # Draw graph
    fig, ax = plt.subplots(figsize=(13, 7))

    node_size = 1000
    edge_style = dict(arrows=True, arrowsize=12, node_size=node_size)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_size)
    nx.draw_networkx_labels(G, pos, labels=formatted_labels, font_size=7)
    nx.draw_networkx_edges(
        G_hard,
        pos,
        edge_color="black",
        **edge_style,
    )

    soft_edges = [
        (u, v) for u, v, d in G.edges(data=True) if d["type"] == "prev_time_dependency"
    ]
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=soft_edges,
        edge_color=(0.5, 0.5, 0.5, 0.4),
        style="dotted",
        connectionstyle="arc3,rad=0.5",
        **edge_style,
    )
    ax.margins(0)

    computed_patch = mpatches.Patch(color=mimosa_green, label="Computed variables")
    input_patch = mpatches.Patch(color=mimosa_orange, label="Input variables")

    plt.legend(
        handles=[computed_patch, input_patch],
        loc="upper center",  # or 'lower left', 'best', etc.
        bbox_to_anchor=(0.5, -0.05),  # place legend outside plot
        ncol=2,
        frameon=False,
    )

    plt.title("MIMOSA variable dependency graph", fontsize=14)
    plt.axis("off")
    plt.tight_layout()
    plt.show()

    return plt


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected in the equations."""

    pass
