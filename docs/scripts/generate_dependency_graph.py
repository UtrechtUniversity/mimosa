"""Generate documentation graphs from the shared, cached documentation models.

MkDocs calls this once per build command or serve session. Only symbolic
constraints are inspected; no simulation or optimisation is performed.
"""

import json
from functools import lru_cache
from types import SimpleNamespace
from urllib.parse import urlencode

import networkx as nx
from networkx.drawing.nx_agraph import to_agraph

from mimosa.common import Var, add_constraint
from mimosa.common.config.parseconfig import check_params
from mimosa.core.simulation.helpers import calc_dependencies
from docs.scripts import variable_docs
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer


def render_graph(graph, context=None):
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

    return drawing.draw(format="svg", prog="dot")


def write_graph(graph, output, context=None):
    """Save an SVG for standalone inspection."""
    output.write_bytes(render_graph(graph, context))
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


def configuration_example(config, defaults):
    """Show the overrides needed to reproduce this graph, omitting defaults."""
    assignments = []

    def visit(options, default_options, path=()):
        for key, value in options.items():
            keys = path + (key,)
            default = default_options.get(key)
            if isinstance(value, dict):
                visit(value, default or {}, keys)
            elif value != default:
                lookup = "".join(f"[{part!r}]" for part in keys)
                assignments.append(f"params{lookup} = {value!r}")

    visit(config, defaults)
    code = "\n".join(["params = load_params()", *assignments, "model = MIMOSA(params)"])
    highlighted = highlight(
        code, PythonLexer(),
        HtmlFormatter(nowrap=True, hl_lines=list(range(2, len(assignments) + 2))),
    )
    return f'<div class="highlight"><pre><code>{highlighted}</code></pre></div>'


def context_graph(context):
    """Inspect the existing model, temporarily attaching baseline equations."""
    model = context.model
    added_constraints = []
    try:
        for equation in context.baseline_equations:
            added_constraints.append(add_constraint(
                model, equation.to_pyomo_constraint(model), equation.name
            ))
        return build_graph(SimpleNamespace(
            concrete_model=model,
            equations=context.equations + context.baseline_equations,
        ))
    finally:
        for name in added_constraints:
            model.del_component(name)


@lru_cache(maxsize=1)
def get_dependency_graph_assets():
    """Cache SVG layouts and their index across all live reloads in a session."""
    assets = {}
    contexts = {}
    defaults = check_params({})
    for name, settings in variable_docs.DOCUMENTATION_CONFIGS.items():
        graph = context_graph(variable_docs.get_documentation_context(name))
        source = f"{name}.svg"
        assets[f"assets/dependency-graphs/{source}"] = render_graph(graph, name)
        contexts[name] = {
            "label": configuration_label(settings),
            "configuration_html": configuration_example(settings, defaults),
            "source": source,
            "variables": sorted(graph),
        }
    manifest = {"default_context": "coacch", "contexts": contexts}
    assets["assets/dependency-graphs/index.json"] = json.dumps(manifest)
    return assets
