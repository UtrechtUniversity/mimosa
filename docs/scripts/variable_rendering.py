"""Render variable documentation after MkDocs has processed component docstrings."""

import re
from html import escape
from html.parser import HTMLParser
from itertools import product
from textwrap import indent

from docs.scripts.variable_availability import availability_requirements
from docs.scripts.variable_docs import get_documentation_context
from docs.scripts.variable_references import (
    group_variables,
    resolve_variable_reference,
    variable_reference_url,
)

REFERENCE_MARKER = "{variables::reference}"
VARIABLE_MARKER = re.compile(r"(?<![\w:])(?:varref|var)::[\w.]*(?:::[\w.]*)*")


def _description(variable):
    return escape(variable.description or "Description not provided.")


def _details(variable):
    unit = variable.unit if variable.has_declared_units else "not declared"
    dimensions = ", ".join(variable.dimensions) or "scalar"
    details = (
        f"Units: <code>{escape(unit)}</code>; "
        f"dimensions: <code>{escape(dimensions)}</code>."
    )
    if variable.requires_baseline:
        details += " Requires a no-policy baseline."
    return f'<span class="variable-metadata">{details}</span>'


def render_variable_reference(catalogue, context_params=None):
    """Render Markdown admonitions, retaining context-specific anchors."""
    all_contexts = {variable.context for variable in catalogue}
    available_contexts = {}
    for variable in catalogue:
        available_contexts.setdefault(variable.name, set()).add(variable.context)

    if context_params is None and any(
        contexts != all_contexts for contexts in available_contexts.values()
    ):
        context_params = {
            context: get_documentation_context(context).params
            for context in sorted(all_contexts)
        }

    entries = []
    for entry in group_variables(catalogue):
        variable = entry.metadata
        anchors = "".join(
            f'<span id="{escape(anchor, quote=True)}"></span>'
            for anchor in entry.anchors
        )
        unit = variable.unit if variable.has_declared_units else "not declared"
        dimensions = ", ".join(variable.dimensions) or "scalar"
        content = [
            anchors,
            "",
            f"<p>{_description(variable)}</p>",
            "",
            f"- Units: <code>{escape(unit)}</code>",
            f"- Dimensions: <code>{escape(dimensions)}</code>",
        ]
        if variable.requires_baseline:
            content.append("- Requires a no-policy baseline.")
        if available_contexts[variable.name] != all_contexts:
            alternatives = availability_requirements(
                available_contexts[variable.name], context_params
            )
            blocks = []
            for requirements in alternatives:
                paths, value_choices = zip(*requirements)
                for values in product(*value_choices):
                    assignments = []
                    for path, value in zip(paths, values):
                        keys = "".join(f"[{key!r}]" for key in path.split("."))
                        assignments.append(f"params{keys} = {value!r}")
                    highlight_lines = " ".join(
                        str(line) for line in range(2, len(assignments) + 2)
                    )
                    blocks.append(
                        "\n".join([
                            f'```python hl_lines="{highlight_lines}"',
                            "params = load_params()",
                            *assignments,
                            "model = MIMOSA(params)",
                            "```",
                        ])
                    )
            content.append("\nAvailable when:\n")
            content.append("\n\nor\n\n".join(blocks))
        title = f'!!! variable "{escape(variable.name)}"\n\n'
        entries.append(title + indent("\n".join(content), "    "))
    return "\n\n".join(entries) + "\n"


def expand_variable_reference(markdown, catalogue):
    """Expand a standalone reference marker, leaving Markdown code examples alone."""
    lines = []
    fence = None
    for line in markdown.splitlines(keepends=True):
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match:
            marker, suffix = match.groups()
            if fence is None:
                fence = marker
            elif (
                marker[0] == fence[0]
                and len(marker) >= len(fence)
                and not suffix.strip()
            ):
                fence = None
        if fence is None and line.rstrip("\r\n") == REFERENCE_MARKER:
            lines.append(render_variable_reference(catalogue) + "\n")
        else:
            lines.append(line)
    return "".join(lines)


class _VariableHTMLRenderer(HTMLParser):
    """Replace markers only in text, preserving code, links and HTML attributes."""

    def __init__(self, catalogue, page_context, page_path, page_url, reference_url):
        super().__init__(convert_charrefs=False)
        self.catalogue = catalogue
        self.page_context = page_context
        self.page_path = page_path
        self.page_url = page_url
        self.reference_url = reference_url
        self.output = []
        self.ignored = []

    def handle_starttag(self, tag, attrs):
        self.output.append(self.get_starttag_text())
        if tag in ("code", "pre", "a", "script", "style"):
            self.ignored.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.output.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        self.output.append(f"</{tag}>")
        if self.ignored and self.ignored[-1] == tag:
            self.ignored.pop()

    def handle_data(self, data):
        self.output.append(
            data if self.ignored else VARIABLE_MARKER.sub(self._replace, data)
        )

    def _replace(self, match):
        # A sentence-ending period is punctuation, not part of a variable name.
        marker = match.group().rstrip(".")
        punctuation = match.group()[len(marker) :]
        variable = resolve_variable_reference(
            marker, self.page_context, self.page_path, self.catalogue
        )
        url = variable_reference_url(variable, self.page_url, self.reference_url)
        link = f'<a href="{escape(url, quote=True)}"><code>{escape(variable.name)}</code></a>'
        if marker.startswith("varref::"):
            return link + punctuation
        return (
            f'<span class="variable-description">{link}: '
            f"{_description(variable)} {_details(variable)}</span>{punctuation}"
        )

    def handle_entityref(self, name):
        self.output.append(f"&{name};")

    def handle_charref(self, name):
        self.output.append(f"&#{name};")

    def handle_comment(self, data):
        self.output.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.output.append(f"<!{decl}>")

    def handle_pi(self, data):
        self.output.append(f"<?{data}>")


def render_variable_markers(
    html, catalogue, page_context, page_path, page_url, reference_url
):
    """Process both page prose and mkdocstrings output with the same renderer."""
    renderer = _VariableHTMLRenderer(
        catalogue, page_context, page_path, page_url, reference_url
    )
    renderer.feed(html)
    renderer.close()
    return "".join(renderer.output)
