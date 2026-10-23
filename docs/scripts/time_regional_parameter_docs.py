"""Reference plots of baseline inputs on the documentation model's time grid."""

import json
from copy import deepcopy
from functools import lru_cache
from html import escape
from textwrap import indent

from pyomo.environ import value

from docs.scripts.variable_docs import get_documentation_context
from mimosa.common.config.parseconfig import parse_param_values
from mimosa.common.pyomo_utils import get_unit


TIME_REGIONAL_REFERENCE_MARKER = "{timeandregionalparams::reference}"
PLOT_DIRECTORY = "assets/parameter-plots"
BASELINE_PARAMETERS = (
    ("population", "population", "Population from the selected socioeconomic scenario."),
    ("baseline_GDP", "GDP", "Baseline GDP from the selected socioeconomic scenario."),
    ("ssp_baseline_emissions", "emissions", "Baseline CO₂ emissions before mitigation."),
)


def create_parameter_plot(model, name):
    """Read initialized values without rerunning interpolation or the model."""
    parameter = getattr(model, name)
    times = [t for t in model.t if 2025 <= value(model.year(t)) <= 2100]
    years = [value(model.year(t)) for t in times]
    regions = list(model.regions)
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines",
                "name": region,
                "x": years,
                "y": [value(parameter[t, region]) for t in times],
                "line": {"color": f"hsl({round(index * 360 / len(regions))}, 60%, 45%)"},
                "hovertemplate": "%{x}: %{y:,.4g}<extra>%{fullData.name}</extra>",
            }
            for index, region in enumerate(regions)
        ],
        "layout": {
            "autosize": True,
            "height": 480,
            "xaxis": {"title": "Year", "range": [2025, 2100]},
            "yaxis": {"title": get_unit(parameter)},
            "legend": {"title": {"text": "Region"}},
            "margin": {"l": 75, "r": 20, "t": 20, "b": 55},
        },
        "config": {"responsive": True, "displaylogo": False},
    }


@lru_cache(maxsize=1)
def get_time_regional_parameter_assets():
    """Generate the three small JSON assets once per build or serve session."""
    model = get_documentation_context().model
    return {
        f"{PLOT_DIRECTORY}/{name}.json": json.dumps(
            create_parameter_plot(model, name), allow_nan=False
        )
        for name, _, _ in BASELINE_PARAMETERS
    }


def render_time_regional_parameter_reference(context):
    params = parse_param_values(deepcopy(context.params))
    sections = []
    for name, source_name, description in BASELINE_PARAMETERS:
        source = params["input"]["variables"][source_name]
        unit = get_unit(getattr(context.model, name))
        content = (
            f'<span id="timeandregional.{name}" class="param_anchor"> </span>\n\n'
            f"{description}\n\n"
            f"- Units: `{escape(unit)}`\n"
            f"- Scenario: {escape(source['scenario'])}\n"
            f"- Source: {escape(source['model'])}, {escape(source['variable'])}\n"
            f"- Data file: `{escape(source['file'])}`\n\n"
            "```plotly\n"
            + json.dumps({"file_path": f"{PLOT_DIRECTORY}/{name}.json"})
            + "\n```\n"
        )
        sections.append(f'??? parameter "{name}"\n\n' + indent(content, "    "))
    return "\n".join(sections)
