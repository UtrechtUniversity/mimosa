"""Variable markers in Markdown, rendered docstrings and complete MkDocs builds."""

from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest
from pyomo.environ import ConcreteModel, Constraint, Var
import yaml

from docs.scripts import variable_docs
from docs.scripts.variable_docs import VariableMetadata
from docs.scripts.variable_rendering import (
    expand_variable_reference,
    render_variable_markers,
    render_variable_reference,
)


@pytest.fixture
def catalogue():
    coacch = VariableMetadata(
        name="damage_costs", description="Damage & adaptation <costs>",
        unit="fraction_of_GDP", dimensions=("t", "regions"),
        context="coacch", has_declared_units=True,
    )
    return (
        coacch,
        replace(coacch, context="coacch_noadaptation"),
        replace(coacch, context="accreu_sectoral", description="Residual damages"),
    )


def render(html, catalogue):
    return render_variable_markers(
        html, catalogue, "coacch", "components/damages/example.md",
        "components/damages/example/", "variables/",
    )


def test_full_entries_and_inline_links_in_prose_and_lists(catalogue):
    html = render(
        "<p>See varref::damage_costs.</p><ul><li>var::damage_costs</li></ul>", catalogue
    )

    assert html.count('href="../../../variables/#variable-coacch--damage_costs"') == 2
    assert html.count("Damage &amp; adaptation &lt;costs&gt;") == 1
    assert "Units: <code>fraction_of_GDP</code>" in html
    assert "dimensions: <code>t, regions</code>" in html
    assert "</a>.</p>" in html
    assert "var::" not in html
    assert "varref::" not in html


@pytest.mark.parametrize(
    "html",
    [
        "<p><code>var::missing</code></p>",
        '<pre><code class="language-text"><span>varref::missing</span></code></pre>',
        '<a href="var::missing">varref::missing</a>',
        '<span title="var::missing">An attribute</span>',
        "<!-- var::missing -->",
        '<script>const marker = "var::missing";</script>',
        '<style>.example::after {content: "var::missing"}</style>',
    ],
)
def test_code_links_attributes_and_noncontent_remain_literal(catalogue, html):
    assert render(html, catalogue) == html


def test_html_entities_and_unrelated_markup_are_preserved(catalogue):
    html = '<p class="example">A &amp; B &#62; C<br />.</p>'
    assert render(html, catalogue) == html


def test_explicit_context_in_rendered_marker_overrides_page(catalogue):
    html = render("<p>var::accreu_sectoral::damage_costs</p>", catalogue)

    assert "Residual damages" in html
    assert "#variable-accreu_sectoral--damage_costs" in html
    assert "Damage &amp; adaptation" not in html


def test_missing_metadata_scalar_and_baseline_requirement_are_visible(catalogue):
    variable = replace(
        catalogue[0], description=None, has_declared_units=False,
        dimensions=(), requires_baseline=True,
    )
    html = render("<p>var::damage_costs</p>", (variable,))

    assert "Description not provided." in html
    assert "Units: <code>not declared</code>" in html
    assert "dimensions: <code>scalar</code>" in html
    assert "Requires a no-policy baseline." in html


def test_reference_keeps_variants_and_all_merged_anchors(catalogue):
    html = render_variable_reference(catalogue)

    assert html.count("<dt>") == 2
    assert html.count("Damage &amp; adaptation &lt;costs&gt;") == 1
    assert html.count("Residual damages") == 1
    for variable in catalogue:
        assert html.count(f'id="variable-{variable.context}--damage_costs"') == 1
        assert f"<code>{variable.context}</code>" in html


def test_reference_placeholder_expands_only_outside_code_examples(catalogue):
    markdown = (
        "# Reference\n\n{variables::reference}\n\n"
        "`{variables::reference}`\n\n"
        "```markdown\n{variables::reference}\n```\n\n"
        "~~~markdown\n{variables::reference}\n~~~\n\n"
        "    {variables::reference}\n"
    )
    rendered = expand_variable_reference(markdown, catalogue)

    assert rendered.count('<dl class="variable-reference">') == 1
    assert rendered.count("{variables::reference}") == 4


@pytest.fixture
def documentation_site(tmp_path, monkeypatch, catalogue):
    """Use real hooks, macros and mkdocstrings, without constructing MIMOSA."""
    pytest.importorskip("mkdocs")
    pytest.importorskip("mkdocstrings")
    pytest.importorskip("mkdocs_macros")
    model = ConcreteModel()
    model.variable = Var()
    model.sample_constraint = Constraint(
        expr=model.variable >= 0, doc="Constraint macros still render."
    )

    @lru_cache(maxsize=None)
    def get_context(context="default"):
        return SimpleNamespace(model=model, parser_tree={}, variables=catalogue)

    @lru_cache(maxsize=1)
    def get_catalogue():
        return catalogue

    monkeypatch.setattr(variable_docs, "get_documentation_context", get_context)
    monkeypatch.setattr(variable_docs, "get_variable_catalogue", get_catalogue)
    source = tmp_path / "docs"
    (source / "components").mkdir(parents=True)
    (source / "index.md").write_text("# Home\n", encoding="utf-8")
    (source / "variables.md").write_text(
        "# Variable reference\n\n{variables::reference}\n", encoding="utf-8"
    )
    page = source / "components" / "example.md"
    page.write_text(
        "---\nvariable_context: coacch\n---\n\n# Example\n\n"
        "Page prose: varref::damage_costs.\n\n- var::damage_costs\n\n"
        "`var::missing_literal`\n\n```text\nvarref::missing_literal\n```\n\n"
        "::: variable_docs_fixture.component\n",
        encoding="utf-8",
    )
    (tmp_path / "variable_docs_fixture.py").write_text(
        'def component():\n'
        '    """Component documentation.\n\n'
        '    Docstring prose: varref::damage_costs.\n\n'
        '    - var::accreu_sectoral::damage_costs\n\n'
        '    {{ sample_constraint }}\n'
        '    """\n',
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parents[2]
    config = {
        "site_name": "Variable rendering test", "strict": True,
        "docs_dir": str(source), "site_dir": str(tmp_path / "site"),
        "nav": ["index.md", "components/example.md", "variables.md"],
        "hooks": [str(root / "docs/scripts/mkdocs_hooks.py")],
        "plugins": [
            {"mkdocstrings": {"handlers": {"python": {"paths": [str(tmp_path)]}}}},
            {"macros": {"module_name": str(root / "docs/scripts/mkdocs_macros")}},
        ],
        "markdown_extensions": ["fenced_code"],
    }
    return SimpleNamespace(root=tmp_path, page=page, config=config)


def build_site(site):
    from mkdocs.commands.build import build
    from mkdocs.config import load_config

    config_path = site.root / "mkdocs.yml"
    config_path.write_text(yaml.safe_dump(site.config), encoding="utf-8")
    build(load_config(str(config_path)))


@pytest.mark.parametrize("directory_urls", [True, False])
def test_strict_site_build_renders_pages_docstrings_and_reference(documentation_site, directory_urls):
    site = documentation_site
    site.config["use_directory_urls"] = directory_urls
    build_site(site)
    page_file = "components/example/index.html" if directory_urls else "components/example.html"
    reference_file = "variables/index.html" if directory_urls else "variables.html"
    html = (site.root / "site" / page_file).read_text(encoding="utf-8")
    reference = (site.root / "site" / reference_file).read_text(encoding="utf-8")
    reference_url = "../../variables/" if directory_urls else "../variables.html"

    assert html.count("Damage &amp; adaptation &lt;costs&gt;") == 1
    assert "Residual damages" in html
    assert "Constraint macros still render." in html
    assert html.count(f'href="{reference_url}#variable-coacch--damage_costs"') == 3
    assert f'href="{reference_url}#variable-accreu_sectoral--damage_costs"' in html
    assert "var::missing_literal" in html
    assert "varref::missing_literal" in html
    assert 'id="variable-coacch_noadaptation--damage_costs"' in reference
    assert "{variables::reference}" not in reference


@pytest.mark.parametrize(
    "content,problem",
    [
        ("var::missing", "Unknown variable 'missing'"),
        ("varref::damage_costs", "Ambiguous variable 'damage_costs'"),
        ("var::missing_context::damage_costs", "Unknown variable context 'missing_context'"),
    ],
)
def test_strict_site_build_fails_with_page_and_reference_error(documentation_site, content, problem):
    site = documentation_site
    site.page.write_text(f"# Invalid reference\n\n{content}\n", encoding="utf-8")

    with pytest.raises(ValueError) as error:
        build_site(site)

    assert "components/example.md" in str(error.value)
    assert problem in str(error.value)
