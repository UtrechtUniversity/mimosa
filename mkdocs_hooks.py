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
    # Build the parameter reference
    return markdown


def on_page_content(html, **kwargs):
    pattern = re.compile(r"param::[a-zA-Z0-9_]+")
    for match in re.findall(pattern, html):
        param_name = match.split("param::")[1]
        try:
            param = getattr(model, param_name)
            if param.doc:
                keys = param.doc.split("::")[1].split(".")
                doc = get_nested(parser_tree, keys).to_string()
                formatted_text = f"<code>{param_name}</code>: {doc}"
            else:
                formatted_text = f"<code>{param_name}</code>"
            html = html.replace(match, formatted_text)

        except AttributeError:
            pass
    return html
