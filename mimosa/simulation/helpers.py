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

    timestep = 1
    for name, eq in equations_dict.items():
        if isinstance(eq, RegionalEquation):
            index = [timestep, "CAN"]
        else:
            index = [timestep]

        expr = str(getattr(m, "constraint_" + name)[*index].expr)
        expr_rhs = expr.split("==")[1]
        variables = set(_extract_variables(expr_rhs, timestep))
        # Only keep variables, not params:
        variables = [v for v in variables if not isinstance(getattr(m, v, None), Param)]

        # Save the dependencies to the equation:
        eq.dependencies = variables


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
    G = nx.DiGraph()

    equations_sorted = []

    # Add edges
    for node, eq in equations_dict.items():
        for dep in eq.dependencies:
            G.add_edge(dep, node)

    # Check for cycles
    cycles = list(nx.simple_cycles(G))
    if cycles:
        error_msg = "Circular dependencies found:\n\n"
        for cycle in cycles:
            error_msg += " -> ".join(cycle) + "\n"
        raise ValueError(error_msg)
    else:
        # Topological sort
        ordered_nodes = list(nx.topological_sort(G))
        for node in ordered_nodes:
            try:
                equations_sorted.append(equations_dict[node])
            except KeyError:
                # print(f"Warning: no equation found for {node}, skipping.")
                pass

    if return_graph:
        return equations_sorted, G
    return equations_sorted


def plot_dependency_graph(G):

    import matplotlib.pyplot as plt

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

    # Use graphviz layout (tree-style, top-down)
    pos = graphviz_layout(G, prog="dot")

    # Draw graph
    plt.figure(figsize=(12, 15))
    nx.draw(
        G,
        pos,
        labels=formatted_labels,
        with_labels=True,
        arrows=True,
        node_size=2500,
        node_color="lightblue",
        font_size=10,
        arrowstyle="->",
        arrowsize=12,
    )
    plt.title("MIMOSA variable dependency graph", fontsize=14)
    plt.axis("off")
    plt.show()
