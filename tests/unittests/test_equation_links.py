"""Equation graph links must refer to concrete variables in the displayed context."""

import ast
from pathlib import Path
import re
from urllib.parse import unquote

import pytest
import yaml

from docs.scripts.variable_docs import get_variable_catalogue
from mimosa.common.config.parseconfig import check_params
from mimosa.common.regional_params import RegionalParamStore

ROOT = Path(__file__).resolve().parents[2]
INCLUDE = re.compile(r"^\s*:::\s*(mimosa\.[\w.]+)", re.MULTILINE)
GRAPH_LINK = re.compile(r"\\href\{\./#var__([^}]+)\}")


@pytest.fixture(scope="module")
def docstrings():
    """Read documentation without importing or executing model components."""
    result = {}
    for path in (ROOT / "mimosa").rglob("*.py"):
        module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                result[f"{module}.{node.name}"] = ast.get_docstring(node) or ""
    return result


def test_equation_links_resolve_in_the_page_or_explicit_context(docstrings):
    available = {(v.context, v.name) for v in get_variable_catalogue()}
    checked = []
    for path in (ROOT / "docs").rglob("*.md"):
        markdown = path.read_text(encoding="utf-8")
        metadata = (
            yaml.safe_load(markdown.split("---", 2)[1])
            if markdown.startswith("---\n") else {}
        )
        page_context = (metadata or {}).get("variable_context", "coacch")
        pending = [markdown]
        included = set()
        while pending:
            content = pending.pop()
            for target in GRAPH_LINK.findall(content):
                parts = target.split("::")
                context, name = parts if len(parts) == 2 else (page_context, target)
                context = "coacch" if context == "default" else context
                assert (context, name) in available, (
                    f"{path.relative_to(ROOT)}: {target} unavailable in {context}"
                )
                checked.append((context, name))
            for name in INCLUDE.findall(content):
                if name in docstrings and name not in included:
                    included.add(name)
                    pending.append(docstrings[name])
    assert checked, "No equation links were checked"


@pytest.mark.parametrize("name", [
    "mimosa.components.welfare.utility_fct.calc_utility",
    "mimosa.components.financialtransfer.notransfer.get_constraints",
    "mimosa.components.effortsharing.equal_cumulative_per_cap._calc_debt",
])
def test_generic_arguments_and_parameters_have_no_variable_links(docstrings, name):
    assert not GRAPH_LINK.search(docstrings[name])


def test_coacch_links_actual_damages_but_not_the_polynomial_definition(docstrings):
    prefix = "mimosa.components.damages.coacch."
    assert GRAPH_LINK.findall(docstrings[prefix + "get_constraints"]) == [
        "damage_costs", "non_slr_damage_costs", "slr_damage_costs",
    ]
    equations = re.findall(
        r"\$\$(.*?)\$\$",
        docstrings[prefix + "get_constraints_temperature_dependent"], re.DOTALL,
    )
    assert not GRAPH_LINK.search(equations[0])
    assert set(GRAPH_LINK.findall(equations[1])) == {"non_slr_damage_costs", "temperature"}


def test_regional_links_in_text_and_equations_match_registered_columns(docstrings):
    params, parsers = check_params({}, return_parser_tree=True)
    store = RegionalParamStore(params, parsers)
    available = {
        f"{category}.{column}"
        for category, container in store.categories.items()
        for column in container.data.columns
    }
    contents = list(docstrings.values()) + [
        path.read_text(encoding="utf-8") for path in (ROOT / "docs").rglob("*.md")
    ]
    checked = []
    for content in contents:
        for target in re.findall(r"#param__regional\.([^\s})\"]+)", content):
            target = unquote(target)
            assert target in available, f"Unknown regional parameter: {target}"
            checked.append(target)
    assert any(target.startswith("ACCREU.") for target in checked)
    assert any("(q=0.5)" in target for target in checked)
