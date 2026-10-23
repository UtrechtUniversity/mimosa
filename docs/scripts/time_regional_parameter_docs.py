"""Discover and plot initialized time-and-region parameters from shared models."""

import json
from copy import deepcopy
from dataclasses import dataclass, replace
from functools import lru_cache
from html import escape
from itertools import groupby
from textwrap import indent
from typing import Optional, Tuple

from pyomo.environ import Param, value

from docs.scripts.variable_availability import render_availability_examples
from docs.scripts import variable_docs
from mimosa.common.config.parseconfig import parse_param_values
from mimosa.common.pyomo_utils import get_indices, get_unit


TIME_REGIONAL_REFERENCE_MARKER = "{timeandregionalparams::reference}"
PLOT_DIRECTORY = "assets/parameter-plots"


@dataclass(frozen=True)
class TimeRegionalParameter:
    """A value snapshot; equal declarations and plotted values share one entry."""

    name: str
    description: Optional[str]
    unit: str
    years: Tuple[float, ...]
    regions: Tuple[str, ...]
    values: Tuple[Tuple[Optional[float], ...], ...]
    contexts: Tuple[str, ...] = ()

    @property
    def source_name(self):
        prefix = "timeandregional::"
        if self.description and self.description.startswith(prefix):
            return self.description[len(prefix):]
        return None


def collect_time_regional_parameters(model):
    """Read public time-and-region parameters with nonzero initialized values.

    Omit zero substitutes and wholly uninitialized parameters. Missing values
    within a retained series stay missing, without requiring a simulation.
    """
    parameters = [
        parameter
        for parameter in sorted(model.component_objects(Param), key=lambda p: p.name)
        if not parameter.name.startswith("_")
        and set(get_indices(parameter)) == {"t", "regions"}
    ]
    if not parameters:
        return ()
    times = [t for t in model.t if 2025 <= value(model.year(t)) <= 2100]
    years = tuple(value(model.year(t)) for t in times)
    regions = tuple(model.regions)
    entries = []
    for parameter in parameters:
        dimensions = get_indices(parameter)
        # Read existing data without creating uninitialized mutable entries.
        numbers = {
            key: value(data, exception=False) for key, data in parameter.items()
        }
        series = []
        for region in regions:
            values = []
            for t in times:
                key = (t, region) if dimensions[0] == "t" else (region, t)
                number = numbers.get(key)
                values.append(float(number) if number is not None else None)
            series.append(tuple(values))
        if not any(
            number is not None and number != 0
            for values in series for number in values
        ):
            continue
        entries.append(TimeRegionalParameter(
            name=parameter.name,
            description=parameter.doc,
            unit=get_unit(parameter),
            years=years,
            regions=regions,
            values=tuple(series),
        ))
    return tuple(entries)


@lru_cache(maxsize=1)
def get_time_regional_parameter_catalogue():
    """Merge identical entries across the already cached documentation models."""
    grouped = {}
    for context_name in variable_docs.DOCUMENTATION_CONFIGS:
        context = variable_docs.get_documentation_context(context_name)
        for entry in collect_time_regional_parameters(context.model):
            grouped.setdefault(entry, []).append(context_name)
    return tuple(sorted(
        (replace(entry, contexts=tuple(contexts)) for entry, contexts in grouped.items()),
        key=lambda entry: entry.name,
    ))


def create_parameter_plot(entry):
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines",
                "name": region,
                "x": entry.years,
                "y": series,
                "line": {"color": f"hsl({round(index * 360 / len(entry.regions))}, 60%, 45%)"},
                "hovertemplate": "%{x}: %{y:,.4g}<extra>%{fullData.name}</extra>",
            }
            for index, (region, series) in enumerate(zip(entry.regions, entry.values))
        ],
        "layout": {
            "autosize": True,
            "height": 480,
            "xaxis": {"title": "Year", "range": [2025, 2100]},
            "yaxis": {"title": entry.unit},
            "legend": {"title": {"text": "Region"}},
            "margin": {"l": 75, "r": 20, "t": 20, "b": 55},
        },
        "config": {"responsive": True, "displaylogo": False},
    }


def parameter_plot_path(entry, variant):
    suffix = "" if variant == 1 else f"-{variant}"
    return f"{PLOT_DIRECTORY}/{entry.name}{suffix}.json"


@lru_cache(maxsize=1)
def get_time_regional_parameter_assets():
    """Plot the values already initialized on the shared SSP2 models."""
    assets = {}
    catalogue = get_time_regional_parameter_catalogue()
    for _, variants in groupby(catalogue, key=lambda entry: entry.name):
        for variant, entry in enumerate(variants, start=1):
            assets[parameter_plot_path(entry, variant)] = json.dumps(
                create_parameter_plot(entry), allow_nan=False
            )
    return assets


def clear_time_regional_parameter_cache():
    get_time_regional_parameter_assets.cache_clear()
    get_time_regional_parameter_catalogue.cache_clear()


def render_time_regional_parameter_reference():
    contexts = {
        name: variable_docs.get_documentation_context(name)
        for name in variable_docs.DOCUMENTATION_CONFIGS
    }
    context_params = {name: context.params for name, context in contexts.items()}
    sections = []
    catalogue = get_time_regional_parameter_catalogue()
    for name, grouped in groupby(catalogue, key=lambda entry: entry.name):
        variants = list(grouped)
        content = [f'<span id="timeandregional.{escape(name)}" class="param_anchor"> </span>']
        for variant, entry in enumerate(variants, start=1):
            context = contexts[entry.contexts[0]]
            if len(variants) > 1:
                content.append(f"**Values {variant}**")
            description = entry.description
            details = [
                f"- Units: `{escape(entry.unit)}`",
                f"- Scenario: {escape(context.params['SSP'])}",
            ]
            if entry.source_name:
                params = parse_param_values(deepcopy(context.params))
                source = params["input"]["variables"][entry.source_name]
                description = context.parser_tree["input"]["variables"][entry.source_name].descr
                details.extend([
                    f"- Source: {escape(source['model'])}, {escape(source['variable'])}",
                    f"- Data file: `{escape(source['file'])}`",
                ])
            content.extend([
                escape(description or "Description not provided."),
                "\n".join(details),
            ])
            examples = render_availability_examples(entry.contexts, context_params)
            if examples:
                content.extend(["Available when:", examples])
            if any(number is None for series in entry.values for number in series):
                content.append("Uninitialised values are shown as gaps.")
            content.append(
                "```plotly\n"
                + json.dumps({"file_path": parameter_plot_path(entry, variant)})
                + "\n```"
            )
        sections.append(f'??? parameter "{escape(name)}"\n\n' + indent("\n\n".join(content), "    "))
    return "\n\n".join(sections)
