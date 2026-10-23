import re
import json
import yaml
import sys, os
import pandas as pd
from html import escape
from urllib.parse import quote

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from docs.scripts.variable_docs import (
    DOCUMENTATION_CONFIGS,
    clear_documentation_cache,
    get_documentation_context,
    get_variable_catalogue,
)
from docs.scripts.variable_rendering import (
    REFERENCE_MARKER,
    expand_variable_reference,
    render_variable_markers,
)
from docs.scripts import generate_dependency_graph
from docs.scripts.regional_parameter_docs import (
    REGIONAL_REFERENCE_MARKER,
    render_regional_parameter_reference,
)
from docs.scripts.time_regional_parameter_docs import (
    TIME_REGIONAL_REFERENCE_MARKER,
    get_time_regional_parameter_assets,
    render_time_regional_parameter_reference,
)
from mimosa.common.regional_params import RegionalParamStore
from mimosa.common.config.parseconfig import (
    get_nested,
    flatten,
    load_default_yaml,
)
from mimosa.common.config.utils.parsers import GeneralParser, PARSER_FACTORY


def markdown_parse_param_reference(markdown):
    """Replace the string "{params::reference} with the list of parameters"""

    # Check if markdown has parameter reference
    check_str = "{params::reference}"
    if check_str not in markdown:
        return markdown

    # Build the parameter reference
    parser_tree = get_documentation_context().parser_tree
    reference_markdown = recursive_param_print(parser_tree, "", [], "")

    # Replace the reference in the markdown
    markdown = markdown.replace(check_str, reference_markdown)

    return markdown


def markdown_parse_parser_types(markdown):
    # Check if markdown has parameter reference
    check_str = "{parsers::types}"
    if check_str not in markdown:
        return markdown

    parser_types_markdown = """
??? info "Parser types"

"""

    flattened_parser_tree = flatten(get_documentation_context().parser_tree)
    default_yaml = load_default_yaml()

    for parser_type, parser in PARSER_FACTORY.parsers.items():
        parser_doc = parser.__doc__.replace("\n", f"\n    ")
        parser_types_markdown += f"""
    ??? parameter "{parser_type}"
        <div id="parser-{parser_type}" markdown class="param_anchor">

    {parser_doc}
        """
        # Get an example: first of this type
        example_key = None
        for key, value in flattened_parser_tree.items():
            if value.type == parser_type:
                example_key = key
                break
        if example_key is not None:
            indent = "        "
            keys = example_key.split(" - ")
            keys_yaml = "".join(
                [
                    (
                        (k + f":\n{indent}" + ("  ") * (i + 1))
                        if i < len(keys) - 1
                        else f"{k}:"
                    )
                    for i, k in enumerate(keys)
                ]
            )
            example_value = get_nested(default_yaml, keys)
            example_value_yaml = str(
                "\n" + yaml.dump(example_value, default_flow_style=False)
            ).replace("\n", f"\n{indent}" + "  " * len(keys))

            n = len(keys_yaml.split("\n"))
            m = len(example_value_yaml.split("\n"))
            highlight_lines = " ".join([str(i) for i in range(n + 1, n + m)])
            parser_types_markdown += f"""
        Example usage:

        ```yaml hl_lines="{highlight_lines}"

        {keys_yaml}{example_value_yaml}

        ```
        </div>
        """

    markdown = markdown.replace(check_str, parser_types_markdown)
    return markdown


def markdown_parse_regional_param_reference(markdown):
    if REGIONAL_REFERENCE_MARKER not in markdown:
        return markdown
    context = get_documentation_context()
    store = RegionalParamStore(context.params, context.parser_tree)
    return markdown.replace(
        REGIONAL_REFERENCE_MARKER, render_regional_parameter_reference(store)
    )


def markdown_parse_time_regional_param_reference(markdown):
    if TIME_REGIONAL_REFERENCE_MARKER not in markdown:
        return markdown
    return markdown.replace(
        TIME_REGIONAL_REFERENCE_MARKER,
        render_time_regional_parameter_reference(get_documentation_context()),
    )


def markdown_parse_region_defs(markdown):
    # Check if markdown has parameter reference
    check_str = "{regions::definitions}"
    if check_str not in markdown:
        return markdown

    path = os.path.join(
        os.path.dirname(__file__),
        "../../mimosa/inputdata/regions/ISO_IMAGE_regions_R5_regions.csv",
    )
    regions = (
        pd.read_csv(path)
        .sort_values("IMAGE region code")[
            ["IMAGE region code", "Region", "Region name"]
        ]
        .drop_duplicates()
    )
    regions_markdown = """

<div class="tiny_table" markdown>
| #  | Region | Region name |
| -- | -- | -- |
"""
    for _, (code, region, name) in regions.iterrows():
        regions_markdown += f"| {code} | {region} | {name} |\n"

    regions_markdown += "\n</div>"
    markdown = markdown.replace(check_str, regions_markdown)
    return markdown


def on_page_markdown(markdown, **kwargs):

    markdown = markdown_parse_param_reference(markdown)
    markdown = markdown_parse_regional_param_reference(markdown)
    markdown = markdown_parse_time_regional_param_reference(markdown)
    markdown = markdown_parse_parser_types(markdown)
    markdown = markdown_parse_region_defs(markdown)
    if REFERENCE_MARKER in markdown:
        markdown = expand_variable_reference(markdown, get_variable_catalogue())

    return markdown


def recursive_param_print(tree, mainkey, breadcrumbs, full_str, level=0):

    # If it is a dictionary, print its keys and call the function recursively
    if isinstance(tree, dict):
        if level > 0:
            title = ""
            if level > 1:
                title = (
                    '<span class="param_group_breadcrumbs">'
                    + (" > ".join(breadcrumbs[:-1]))
                    + " > </span>"
                )
            title += f"{mainkey}"
            extra_str = f"""
<div id="{mainkey}" class="param_group" markdown>
{"#" * (level + 2)} {title} {{data-toc-label="{mainkey}"}}
<div class="param_content" markdown>
"""
        else:
            extra_str = ""
        for key, value in tree.items():
            extra_str += recursive_param_print(
                value, key, breadcrumbs + [key], full_str, level + 1
            )
        full_str += extra_str + "</div></div>"
        return full_str

    # If it is a parameter (leaf of the tree), print its characteristics
    return _print_param(tree, mainkey, breadcrumbs)


def _print_param(tree, mainkey, breadcrumbs, indent=""):
    usage_target = "params" + "".join(f"[{json.dumps(key)}]" for key in breadcrumbs)
    # Print characteristics of parameter
    extra_str = f'{indent}??? parameter "{mainkey}"\n'
    extra_str += f'{indent}    <span id="{".".join(breadcrumbs)}" class="param_anchor"> </span>\n'
    if tree.type == "enum":
        extra_str += GeneralParser.to_markdown(tree, indent + "    ")
        extra_str += f"\n{indent}    - Allowed values:\n"
        for value in tree.allowed_values:
            assignment = f"{usage_target} = {_python_literal(value)}"
            # Autorefs treats adjacent dictionary keys as Markdown link references.
            copy_text = (
                escape(assignment, quote=True)
                .replace("[", "&#91;")
                .replace("]", "&#93;")
            )
            extra_str += (
                f'{indent}        - <span class="param-enum-option">{escape(str(value))}'
                f'<button class="md-clipboard" type="button" '
                f'title="Copy parameter assignment" aria-label="Copy assignment for {escape(str(value), quote=True)}" '
                f'data-clipboard-text="{copy_text}"></button></span>\n'
            )
    else:
        extra_str += tree.to_markdown(indent + "    ")
    extra_str += "\n\n"

    # Add usage example
    extra_str += f"{indent}    Example usage: \n\n"
    extra_str += f"""
{indent}    ```python hl_lines="2"
{indent}    params = load_params()
{indent}    {usage_target} = {_python_literal(tree.default)}
{indent}    model = MIMOSA(params)
{indent}    ```
"""
    return extra_str


def _python_literal(value):
    """Keep strings double-quoted while preserving Python literals for other types."""
    return (
        json.dumps(value, ensure_ascii=False) if isinstance(value, str) else repr(value)
    )


def on_page_content(html, **kwargs):
    context = get_documentation_context()
    model, parser_tree = context.model, context.parser_tree
    pattern = re.compile(r"(param::([a-zA-Z0-9_]+))")
    for match, param_name in re.findall(pattern, html):
        try:
            param = getattr(model, param_name)
            formatted_text = f"<code>{param_name}</code>"
            if isinstance(param.doc, str):
                if param.doc.startswith("regional::"):
                    source = param.doc.split("::", 1)[1]
                    target = quote(f"regional.{source}", safe=".")
                    formatted_text = f"<a href='#param__{target}'><code>{param_name}</code></a>"
                elif param.doc.startswith("::"):
                    keys = param.doc.split("::")[1].split(".")
                    keys_param_format = "".join([f'["{key}"]' for key in keys])
                    doc = get_nested(parser_tree, keys).to_string()
                    target = quote(param.doc.split("::")[1], safe=".")
                    formatted_text = f"<a href='#param__{target}'><code>params{keys_param_format}</code></a>: {doc}"
            html = html.replace(match, formatted_text)

        except AttributeError:
            pass
    # Manual parameters
    pattern = re.compile(r"(manualparam::([a-zA-Z0-9_ ]+)::([a-zA-Z0-9_. ]+)::)")
    for match, param_title, param_key_str in re.findall(pattern, html):
        try:
            formatted_text = f"<code>{param_title}</code>"
            keys = param_key_str.split(".")
            keys_param_format = "".join([f'["{key}"]' for key in keys])
            doc = get_nested(parser_tree, keys).to_string()
            target = quote(param_key_str, safe=".")
            formatted_text = f"<a href='#param__{target}'><code>params{keys_param_format}</code></a>: {doc}"
            html = html.replace(match, formatted_text)

        except AttributeError:
            pass
    if "var::" in html or "varref::" in html:
        page = kwargs["page"]
        reference = kwargs["files"].get_file_from_path("variables.md")
        if reference is None:
            raise ValueError(
                f"{page.file.src_uri}: Variable reference page variables.md is missing"
            )
        html = render_variable_markers(
            html,
            get_variable_catalogue(),
            page.meta.get("variable_context"),
            page.file.src_uri,
            page.url,
            reference.url,
        )
    if "page" in kwargs:
        page = kwargs["page"]
        graph_context = page.meta.get("variable_context") or "coacch"
        if graph_context == "default":
            graph_context = "coacch"
        if graph_context not in DOCUMENTATION_CONFIGS:
            raise ValueError(
                f"{page.file.src_uri}: Unknown variable context {graph_context!r}"
            )
        html += f'<span hidden data-documentation-context="{escape(graph_context, quote=True)}"></span>'
    return html


def on_startup(**kwargs):
    # Start each build command or serve session with fresh model metadata.
    generate_dependency_graph.get_dependency_graph_assets.cache_clear()
    get_time_regional_parameter_assets.cache_clear()
    clear_documentation_cache()


def on_shutdown(**kwargs):
    generate_dependency_graph.get_dependency_graph_assets.cache_clear()
    get_time_regional_parameter_assets.cache_clear()
    clear_documentation_cache()


import time


def on_pre_build(**kwargs):
    # Reuse the catalogue across live rebuilds within the same serve session.
    get_variable_catalogue()


def on_files(files, config, **kwargs):
    from mkdocs.structure.files import File

    # Virtual files go straight to the site, avoiding watched source changes.
    for (
        path,
        content,
    ) in generate_dependency_graph.get_dependency_graph_assets().items():
        files.append(File.generated(config, path, content=content))
    for path, content in get_time_regional_parameter_assets().items():
        files.append(File.generated(config, path, content=content))
    return files
