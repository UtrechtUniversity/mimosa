"""Variable markers in Markdown, rendered docstrings and complete MkDocs builds."""

from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from types import SimpleNamespace

import pytest
from pyomo.environ import ConcreteModel, Constraint, Var
import yaml

from docs.scripts import variable_docs
from mimosa.common.config.parseconfig import check_params
from docs.scripts.variable_docs import VariableMetadata
from docs.scripts.variable_rendering import (
    expand_variable_reference,
    render_variable_markers,
    render_variable_reference,
)


@pytest.fixture
def catalogue():
    coacch = VariableMetadata(
        name="damage_costs",
        description="Damage & adaptation <costs>",
        unit="fraction_of_GDP",
        dimensions=("t", "regions"),
        context="coacch",
        has_declared_units=True,
    )
    return (
        coacch,
        replace(coacch, context="coacch_noadaptation"),
        replace(coacch, context="accreu_sectoral", description="Residual damages"),
    )


def render(html, catalogue):
    return render_variable_markers(
        html,
        catalogue,
        "coacch",
        "components/damages/example.md",
        "components/damages/example/",
        "variables/",
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
        catalogue[0],
        description=None,
        has_declared_units=False,
        dimensions=(),
        requires_baseline=True,
    )
    html = render("<p>var::damage_costs</p>", (variable,))

    assert "Description not provided." in html
    assert "Units: <code>not declared</code>" in html
    assert "dimensions: <code>scalar</code>" in html
    assert "Requires a no-policy baseline." in html


def test_reference_keeps_variants_and_all_merged_anchors(catalogue):
    html = render_variable_reference(catalogue)

    assert html.count('!!! variable "damage_costs"') == 2
    assert "    !!! variable" not in html
    assert html.count("Damage &amp; adaptation &lt;costs&gt;") == 1
    assert html.count("Residual damages") == 1
    # This variable exists everywhere, despite its different descriptions.
    assert "Available when:" not in html
    assert "Example usage:" not in html
    for variable in catalogue:
        assert html.count(f'id="variable-{variable.context}--damage_costs"') == 1
        assert (
            f'id="variable-{variable.context}--damage_costs" class="variable_anchor"'
            in html
        )


def test_reference_example_sets_all_required_options(catalogue):
    conditional = replace(
        catalogue[0], name="monetary_mortality", context="accreu_sectoral"
    )
    context_params = {
        "coacch": check_params({}),
        "coacch_noadaptation": check_params(
            {
                "model structure": {"damage module": "ACCREU"},
                "economics": {"damages": {"accreu": {"monetise_mortality": False}}},
            }
        ),
        "accreu_sectoral": check_params(
            {"model structure": {"damage module": "ACCREU"}}
        ),
    }

    rendered = render_variable_reference(catalogue + (conditional,), context_params)

    assert "params['model structure']['damage module'] = 'ACCREU'" in rendered
    assert (
        "params['economics']['damages']['accreu']['monetise_mortality'] = True"
        in rendered
    )
    assert '```python hl_lines="2 3"' in rendered


def test_reference_placeholder_expands_only_outside_code_examples(catalogue):
    markdown = (
        "# Reference\n\n{variables::reference}\n\n"
        "`{variables::reference}`\n\n"
        "```markdown\n{variables::reference}\n```\n\n"
        "~~~markdown\n{variables::reference}\n~~~\n\n"
        "    {variables::reference}\n"
    )
    rendered = expand_variable_reference(markdown, catalogue)

    assert rendered.count('!!! variable "damage_costs"') == 2
    assert rendered.count("{variables::reference}") == 4


@pytest.fixture
def documentation_site(tmp_path, monkeypatch, catalogue):
    """Use real hooks, macros and mkdocstrings, without constructing MIMOSA."""
    pytest.importorskip("mkdocs")
    pytest.importorskip("mkdocstrings")
    pytest.importorskip("mkdocs_macros")
    from mkdocs.config.config_options import Hooks

    # MkDocs retains hook modules between configurations; each test supplies
    # fresh fake providers, which must be bound when its hook module is loaded.
    Hooks._load_hook.cache_clear()
    model = ConcreteModel()
    model.variable = Var()
    model.sample_constraint = Constraint(
        expr=model.variable >= 0, doc="Constraint macros still render."
    )
    context_constructions = []
    catalogue_collections = []

    @lru_cache(maxsize=None)
    def get_context(context="default"):
        context_constructions.append(context)
        return SimpleNamespace(model=model, parser_tree={}, variables=catalogue)

    @lru_cache(maxsize=1)
    def get_catalogue():
        catalogue_collections.append(True)
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
        "def component():\n"
        '    """Component documentation.\n\n'
        "    Docstring prose: varref::damage_costs.\n\n"
        "    - var::accreu_sectoral::damage_costs\n\n"
        "    {{ sample_constraint }}\n"
        '    """\n',
        encoding="utf-8",
    )
    root = Path(__file__).resolve().parents[2]
    config = {
        "site_name": "Variable rendering test",
        "strict": True,
        "docs_dir": str(source),
        "site_dir": str(tmp_path / "site"),
        "nav": ["index.md", "components/example.md", "variables.md"],
        "hooks": [str(root / "docs/scripts/mkdocs_hooks.py")],
        "plugins": [
            {"mkdocstrings": {"handlers": {"python": {"paths": [str(tmp_path)]}}}},
            {"macros": {"module_name": str(root / "docs/scripts/mkdocs_macros")}},
        ],
        "markdown_extensions": [
            "admonition",
            "pymdownx.details",
            "pymdownx.superfences",
        ],
    }
    return SimpleNamespace(
        root=tmp_path,
        page=page,
        config=config,
        context_constructions=context_constructions,
        catalogue_collections=catalogue_collections,
        get_context=get_context,
        get_catalogue=get_catalogue,
    )


def build_site(site):
    from mkdocs.commands.build import build
    from mkdocs.config import load_config

    config_path = site.root / "mkdocs.yml"
    config_path.write_text(yaml.safe_dump(site.config), encoding="utf-8")
    build(load_config(str(config_path)))


@pytest.mark.parametrize("directory_urls", [True, False])
def test_strict_site_build_renders_pages_docstrings_and_reference(
    documentation_site, directory_urls
):
    site = documentation_site
    site.config["use_directory_urls"] = directory_urls
    build_site(site)
    page_file = (
        "components/example/index.html" if directory_urls else "components/example.html"
    )
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
    assert reference.count('<div class="admonition variable">') == 2
    assert '<p class="admonition-title">damage_costs</p>' in reference
    assert "<li>Units: <code>fraction_of_GDP</code></li>" in reference
    assert "<li>Dimensions: <code>t, regions</code></li>" in reference
    assert "!!! variable" not in reference
    assert "{variables::reference}" not in reference


def test_serve_reuses_models_after_successful_failed_and_recovered_rebuilds(
    documentation_site, monkeypatch
):
    from importlib import import_module

    serve_module = import_module("mkdocs.commands.serve")
    site = documentation_site

    class LiveReloadServer:
        """Drive the real serve lifecycle without opening a network server."""

        def __init__(self, builder, root, **kwargs):
            self.builder = builder
            self.root = Path(root)

        def watch(self, *args, **kwargs):
            pass

        def shutdown(self):
            pass

        def serve(self, **kwargs):
            original_context = site.get_context()
            assert len(site.context_constructions) == 1
            assert len(site.catalogue_collections) == 1

            site.page.write_text("# Updated page\n\nUpdated prose.\n", encoding="utf-8")
            self.builder()
            html = (self.root / "components/example/index.html").read_text(
                encoding="utf-8"
            )
            assert "Updated prose." in html

            site.page.write_text("# Invalid page\n\nvar::missing\n", encoding="utf-8")
            with pytest.raises(ValueError, match="Unknown variable 'missing'"):
                self.builder()

            site.page.write_text(
                "# Recovered page\n\nvar::coacch::damage_costs\n", encoding="utf-8"
            )
            self.builder()
            html = (self.root / "components/example/index.html").read_text(
                encoding="utf-8"
            )
            assert "Damage &amp; adaptation &lt;costs&gt;" in html
            assert site.get_context() is original_context
            assert len(site.context_constructions) == 1
            assert len(site.catalogue_collections) == 1

    monkeypatch.setattr(serve_module, "LiveReloadServer", LiveReloadServer)
    config_path = site.root / "mkdocs.yml"
    config_path.write_text(yaml.safe_dump(site.config), encoding="utf-8")
    serve_module.serve(config_file=str(config_path))

    assert site.get_context.cache_info().currsize == 0
    assert site.get_catalogue.cache_info().currsize == 0


@pytest.mark.parametrize(
    "content,problem",
    [
        ("var::missing", "Unknown variable 'missing'"),
        ("varref::damage_costs", "Ambiguous variable 'damage_costs'"),
        (
            "var::missing_context::damage_costs",
            "Unknown variable context 'missing_context'",
        ),
    ],
)
def test_strict_site_build_fails_with_page_and_reference_error(
    documentation_site, content, problem
):
    site = documentation_site
    site.page.write_text(f"# Invalid reference\n\n{content}\n", encoding="utf-8")

    with pytest.raises(ValueError) as error:
        build_site(site)

    assert "components/example.md" in str(error.value)
    assert problem in str(error.value)
