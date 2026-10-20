"""Render all registered regional inputs using the model's region mapping."""

from html import escape
from numbers import Real
from textwrap import indent
from urllib.parse import quote

import pandas as pd


REGIONAL_REFERENCE_MARKER = "{regionalparams::reference}"


def _cell(value):
    if pd.isna(value):
        return "—"
    text = format(value, ".6g") if isinstance(value, Real) else str(value)
    return escape(text).replace("|", "&#124;").replace("\n", "<br>")


def render_regional_parameter_reference(store):
    """Include every source column, not just those selected by a model module."""
    regions = tuple(store.regions)
    header = "| " + " | ".join(_cell(region) for region in regions) + " |"
    separator = "| " + " | ".join("---" for region in regions) + " |"
    sections = []
    for category, container in store.categories.items():
        sections.append(
            f"### {escape(category)} {{#regional-{quote(category, safe='')}}}\n"
        )
        for name in container.data.columns:
            target = escape(f"regional.{category}.{name}", quote=True)
            values = store.get(category, name)
            row = "| " + " | ".join(_cell(values[region]) for region in regions) + " |"
            content = (
                '<div class="tiny_table regional-parameter-values" markdown="1">\n\n'
                f"{header}\n{separator}\n{row}\n\n</div>"
            )
            sections.append(
                f'??? parameter "{escape(name, quote=True)}"\n\n'
                f'    <span id="{target}" class="param_anchor"> </span>\n\n'
                + indent(content, "    ")
                + "\n"
            )
    return "\n".join(sections)
