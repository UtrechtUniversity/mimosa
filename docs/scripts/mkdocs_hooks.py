import re
import yaml
import sys, os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from mimosa import MIMOSA
from mimosa.common.config.parseconfig import (
    get_nested,
    check_params,
    flatten,
    load_default_yaml,
)
from mimosa.common.config.utils.parsers import PARSER_FACTORY

# Get the default parameters and the parser tree
params, parser_tree = check_params({}, return_parser_tree=True)

# Create an instance of the MIMOSA model to get the names of each parameter to be parsed
model = MIMOSA(params).concrete_model


def markdown_parse_param_reference(markdown):
    """Replace the string "{params::reference} with the list of parameters"""

    # Check if markdown has parameter reference
    check_str = "{params::reference}"
    if check_str not in markdown:
        return markdown

    # Build the parameter reference
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

    flattened_parser_tree = flatten(parser_tree)
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
    markdown = markdown_parse_parser_types(markdown)
    markdown = markdown_parse_region_defs(markdown)

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
{"#" * (level + 1)} {title} {{data-toc-label="{mainkey}"}}
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
    # Print characteristics of parameter
    extra_str = f'{indent}??? parameter "{mainkey}"\n'
    extra_str += f'{indent}    <span id="{".".join(breadcrumbs)}" class="param_anchor"> </span>\n'
    extra_str += tree.to_markdown(indent + "    ") + "\n\n"

    # Add usage example
    extra_str += f"{indent}    Example usage: \n\n"
    _usage_keys = [f'["{key}"]' for key in breadcrumbs]
    _usage_default_val = tree.default
    if isinstance(tree.default, str):
        _usage_default_val = f'"{tree.default}"'
    extra_str += f"""
{indent}    ```python hl_lines="2"
{indent}    params = load_params()
{indent}    params{''.join(_usage_keys)} = {_usage_default_val}
{indent}    model = MIMOSA(params)
{indent}    ```
"""
    return extra_str


def on_page_content(html, **kwargs):
    pattern = re.compile(r"(param::([a-zA-Z0-9_]+))")
    for match, param_name in re.findall(pattern, html):
        try:
            param = getattr(model, param_name)
            formatted_text = f"<code>{param_name}</code>"
            if isinstance(param.doc, str):
                if param.doc.startswith("::"):
                    # Ignore the regional parameters for now
                    keys = param.doc.split("::")[1].split(".")
                    doc = get_nested(parser_tree, keys).to_string()
                    formatted_text = f"<a href='../../parameters/#{param.doc.split('::')[1]}'><code>{param_name}</code></a>: {doc}"
            html = html.replace(match, formatted_text)

        except AttributeError:
            pass
    # Manual parameters
    pattern = re.compile(r"(manualparam::([a-zA-Z0-9_ ]+)::([a-zA-Z0-9_.]+))")
    for match, param_title, param_key_str in re.findall(pattern, html):
        try:
            formatted_text = f"<code>{param_title}</code>"
            # Ignore the regional parameters for now
            keys = param_key_str.split(".")
            doc = get_nested(parser_tree, keys).to_string()
            formatted_text = f"<a href='../../parameters/#{param_key_str}'><code>{param_title}</code></a>: {doc}"
            html = html.replace(match, formatted_text)

        except AttributeError:
            pass
    return html
