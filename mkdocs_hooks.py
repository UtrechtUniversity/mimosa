import re
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from mimosa import MIMOSA
from mimosa.common.config.parseconfig import get_nested, check_params

# Get the default parameters and the parser tree
params, parser_tree = check_params({}, return_parser_tree=True)

# Create an instance of the MIMOSA model to get the names of each parameter to be parsed
model = MIMOSA(params).concrete_model


def on_page_markdown(markdown, **kwargs):
    # Check if markdown has parameter reference
    check_str = "{params::reference}"
    if check_str not in markdown:
        return markdown

    # Build the parameter reference
    reference_markdown = recursive_param_print(parser_tree, "", [], "")
    # for key, parser in parser_tree.items():
    #     reference_markdown += f"## {key}\n"
    #     # reference_markdown += f"{parser.to_string()}\n\n"

    # Replace the reference in the markdown
    markdown = markdown.replace(check_str, reference_markdown)

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
    pattern = re.compile(r"param::[a-zA-Z0-9_]+")
    for match in re.findall(pattern, html):
        param_name = match.split("param::")[1]
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
    return html
