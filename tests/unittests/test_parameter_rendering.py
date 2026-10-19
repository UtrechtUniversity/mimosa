"""Copyable enum assignments in the generated parameter reference."""

from html.parser import HTMLParser

import markdown
from mkdocs_autorefs import AutorefsExtension
import pytest

from docs.scripts.mkdocs_hooks import _print_param
from mimosa.common.config.utils.parsers import EnumParser, IntParser


class CopyButtons(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.buttons = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "button":
            self.buttons.append(dict(attrs))


@pytest.mark.parametrize(
    "keys, values",
    [
        (
            ["economics", "damages", "accreu", "adaptation_determination"],
            ["solver_control", "analytical_optimum"],
        ),
        (
            ['quotes" & <tags>', "option"],
            ["a 'quoted' \"value\" & <tag>\\path", True, 2, None],
        ),
    ],
)
def test_enum_buttons_copy_complete_valid_python_assignments(keys, values):
    parser = EnumParser({"type": "enum", "default": values[0], "values": values})
    source = _print_param(parser, keys[-1], keys)
    html = markdown.markdown(
        source,
        extensions=[
            "admonition", "pymdownx.details", "pymdownx.superfences", AutorefsExtension()
        ],
    )
    buttons = CopyButtons(html).buttons

    assert len(buttons) == len(values)
    assert "<autoref" not in html
    for button, value in zip(buttons, values):
        assert button["class"] == "md-clipboard"
        assert button["type"] == "button"
        assert button["aria-label"] == f"Copy assignment for {value}"
        params = {}
        leaf = params
        for key in keys[:-1]:
            leaf[key] = {}
            leaf = leaf[key]
        exec(button["data-clipboard-text"], {"params": params})
        assert leaf[keys[-1]] == value

    assert "Example usage:" in html
    assert "model = MIMOSA(params)" in source
    # The model parser's own representation remains unchanged.
    assert "data-clipboard" not in parser.to_markdown("")


def test_other_parameter_types_have_no_option_copy_buttons():
    parser = IntParser({"type": "int", "default": 2025})
    source = _print_param(parser, "start", ["time", "start"])
    assert "data-clipboard" not in source
    assert 'params["time"]["start"] = 2025' in source
