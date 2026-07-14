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

    def _get_first_index_with_timestep(keys, timestep):
        for key in keys:
            if isinstance(key, tuple) and key[0] == timestep:
                return key
            elif key == timestep:
                return key
        return None

    timestep = 1
    for name, eq in equations_dict.items():

        constraint_expr = getattr(m, "constraint_" + name)
        index = _get_first_index_with_timestep(constraint_expr.keys(), timestep)
        expr = str(constraint_expr[index].expr)
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

    # Every equation must be present in the hard-dependency graph so that it is
    # included in the simulation execution order, even when it has no variable
    # dependencies and no downstream consumers. Isolated equations are not
    # added to G_full, which is the graph used for plotting.
    G.add_nodes_from(equations_dict)

    # Add edges
    for node, eq in equations_dict.items():
        for dep in eq.dependencies:
            G.add_edge(dep, node)
            G_full.add_edge(dep, node, type="dependency")
        for prev_dep in eq.prev_time_dependencies:
            G_full.add_edge(prev_dep, node, type="prev_time_dependency")

    cycles = list(nx.simple_cycles(G))
    control_variables = []
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
                if node in G_full:
                    G_full.nodes[node]["has_equation"] = True
            except KeyError:
                # print(f"Warning: no equation found for {node}, skipping.")
                G_full.nodes[node]["has_equation"] = False
                control_variables.append(node)

    if return_graph:
        return equations_sorted, G_full, control_variables
    return equations_sorted


def plot_dependency_graph(G, group_depth=2):

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import networkx as nx

    try:
        from networkx.drawing.nx_agraph import to_agraph
    except ImportError:
        raise ImportError("Please install pygraphviz: pip install pygraphviz")

    def _split_at_middle_underscore(s):
        underscores = [i for i, c in enumerate(s) if c == "_"]
        if not underscores:
            return s
        middle = underscores[len(underscores) // 2]
        return s[:middle] + "\n" + s[middle + 1 :]

    def _group_key(node):
        """
        Groups variables by their first `group_depth` underscore-separated parts.

        Example:
        adaptation_costs_abs_riverine  -> adaptation_costs_abs
        adaptation_costs_abs_labourprod -> adaptation_costs_abs
        damage_costs_gross_riverine     -> damage_costs_gross
        damage_costs_gross_labourprod   -> damage_costs_gross
        """
        parts = node.split("_")
        if len(parts) <= group_depth:
            return None
        return "_".join(parts[:group_depth])

    formatted_labels = {node: _split_at_middle_underscore(node) for node in G.nodes}

    # Only hard dependencies are used for the layout
    G_hard = nx.DiGraph()
    G_hard.add_nodes_from(G.nodes(data=True))

    hard_edges = [(u, v) for u, v, d in G.edges(data=True) if d["type"] == "dependency"]
    G_hard.add_edges_from(hard_edges)

    # Convert to pygraphviz AGraph so we can add clusters
    A = to_agraph(G_hard)

    A.graph_attr.update(
        rankdir="LR",
        concentrate="true",
        nodesep="0.5",
        ranksep="1.2",
        compound="true",
    )

    # Build clusters based on variable names
    groups = {}
    for node in G_hard.nodes:
        key = _group_key(node)
        if key is not None:
            groups.setdefault(key, []).append(node)

    # Only create clusters with at least 2 nodes
    for key, nodes in groups.items():
        if len(nodes) < 2:
            continue

        A.add_subgraph(
            nodes,
            name=f"cluster_{key}",
            label=key,
            color="lightgrey",
            style="dashed",
        )

    # Run Graphviz layout
    A.layout(prog="dot")

    # Extract positions back into a dict for NetworkX drawing
    pos = {}
    for node in A.nodes():
        x, y = node.attr["pos"].split(",")
        pos[str(node)] = (float(x), float(y))

    mimosa_green = "#89a041"
    mimosa_orange = "#ed6a2f"

    node_colors = [
        mimosa_green if G.nodes[node].get("has_equation", False) else mimosa_orange
        for node in G.nodes
    ]

    fig, ax = plt.subplots(figsize=(13, 9))

    node_size = 1000
    edge_style = dict(arrows=True, arrowsize=12, node_size=node_size)

    nx.draw_networkx_nodes(
        G,
        pos,
        node_color=node_colors,
        node_size=node_size,
        ax=ax,
    )

    nx.draw_networkx_labels(
        G,
        pos,
        labels=formatted_labels,
        font_size=7,
        ax=ax,
    )

    nx.draw_networkx_edges(
        G_hard,
        pos,
        edge_color="black",
        ax=ax,
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
        ax=ax,
        **edge_style,
    )

    input_patch = mpatches.Patch(color=mimosa_orange, label="Control variables")
    computed_patch = mpatches.Patch(color=mimosa_green, label="Computed variables")

    ax.legend(
        handles=[input_patch, computed_patch],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        ncol=2,
        frameon=False,
    )

    ax.set_title("MIMOSA variable dependency graph", fontsize=14)
    ax.axis("off")
    ax.margins(0)

    plt.tight_layout()
    plt.show()

    return fig


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected in the equations."""

    pass
