"""Regional reference tables use mapped inputs and include unselected columns."""

import csv
from types import SimpleNamespace
from xml.etree import ElementTree

import pytest

from docs.scripts import mkdocs_hooks
from docs.scripts.regional_parameter_docs import (
    REGIONAL_REFERENCE_MARKER,
    render_regional_parameter_reference,
)
from mimosa.common.config.parseconfig import check_params
from mimosa.common.regional_params import RegionalParamStore


def rendered_tree(source):
    markdown = pytest.importorskip("markdown", reason="Rendering tests require .[docs]")
    pytest.importorskip("pymdownx.details", reason="Rendering tests require .[docs]")
    html = markdown.markdown(
        source,
        extensions=["admonition", "pymdownx.details", "md_in_html", "tables", "attr_list"],
    )
    return ElementTree.fromstring(f"<root>{html}</root>")


def table_rows(card):
    return [["".join(cell.itertext()) for cell in row] for row in card.findall(".//tr")]


@pytest.fixture
def regional_store(tmp_path):
    source = tmp_path / "values.csv"
    with source.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["region", "coefficient", "alternative", "form", "missing", "tiny"])
        writer.writerows([
            ["N1", 2, 8, "<linear> & a|b", None, 1.23456789e-9],
            ["N2", 4, 10, "quadratic", None, 1.23456789e-9],
            ["S", 9, 20, "cubic", 7, 0],
        ])
    mapping = tmp_path / "mapping.csv"
    mapping.write_text("SOURCE,IMAGE26\nN1,CAN\nN2,CAN\nS,USA\n")
    params = {
        "regionstype": "IMAGE26",
        "regions": {"USA": {"example": {"coefficient": 12}}, "CAN": {}},
        "regional_parameter_files": {
            "example": {"filename": str(source), "regionstype": "SOURCE"},
        },
        "regionsmappings": [{
            "regionstype1": "SOURCE", "regionstype2": "IMAGE26",
            "conversiontable": str(mapping),
        }],
    }
    return RegionalParamStore(params, {})


def test_tables_preserve_region_order_mapped_values_and_all_alternatives(regional_store):
    tree = rendered_tree(render_regional_parameter_reference(regional_store))
    cards = {card.findtext("summary"): card for card in tree.findall("details")}

    assert set(cards) == {"coefficient", "alternative", "form", "missing", "tiny"}
    # The model mapping averages N1/N2 into CAN; manual overrides still take priority.
    assert table_rows(cards["coefficient"]) == [["USA", "CAN"], ["12", "3"]]
    assert table_rows(cards["alternative"]) == [["USA", "CAN"], ["20", "9"]]
    assert table_rows(cards["form"]) == [["USA", "CAN"], ["cubic", "<linear> & a|b"]]
    assert table_rows(cards["missing"]) == [["USA", "CAN"], ["7", "—"]]
    assert table_rows(cards["tiny"]) == [["USA", "CAN"], ["0", "1.23457e-09"]]
    assert tree.findall(".//a") == []
    assert all("open" not in card.attrib for card in cards.values())
    assert tree.find("h3").get("id") == "regional-example"


def test_default_reference_covers_all_registered_columns_and_26_image_regions():
    params, parser_tree = check_params({}, return_parser_tree=True)
    store = RegionalParamStore(params, parser_tree)
    tree = rendered_tree(render_regional_parameter_reference(store))
    cards = tree.findall("details")

    assert params["regionstype"] == "IMAGE26"
    assert len(params["regions"]) == 26
    assert len(cards) == sum(len(category.data.columns) for category in store.categories.values())
    assert [heading.text for heading in tree.findall("h3")] == list(store.categories)
    for card in cards:
        rows = table_rows(card)
        assert len(rows) == 2
        assert rows[0] == list(params["regions"])
        assert len(rows[1]) == 26
    anchors = [anchor.get("id") for anchor in tree.findall('.//span[@class="param_anchor"]')]
    assert len(anchors) == len(cards)
    assert len(set(anchors)) == len(cards)
    assert "regional.COACCH.NoSLR_b1" in anchors
    assert "regional.ACCREU_CGE.NoSLR_b1" in anchors
    assert "regional.COACCH.NoSLR_a (q=0.025)" in anchors
    titles = [card.findtext("summary") for card in cards]
    assert "kappa_rel_abatement_0.75_2050" in titles
    assert "NoSLR_a (q=0.025)" in titles


def test_hook_expands_regional_marker_only_when_present(monkeypatch, regional_store):
    calls = []

    def context():
        calls.append(True)
        return SimpleNamespace(params=regional_store.params, parser_tree={})

    monkeypatch.setattr(mkdocs_hooks, "get_documentation_context", context)
    assert mkdocs_hooks.on_page_markdown("Ordinary page") == "Ordinary page"
    assert calls == []
    result = mkdocs_hooks.on_page_markdown(REGIONAL_REFERENCE_MARKER)
    assert REGIONAL_REFERENCE_MARKER not in result
    assert table_rows(rendered_tree(result).find("details")) == [["USA", "CAN"], ["12", "3"]]
    assert calls == [True]


def test_regional_parameter_marker_links_to_its_source(monkeypatch):
    context = SimpleNamespace(
        model=SimpleNamespace(factor=SimpleNamespace(doc="regional::MAC.kappa_rel_abatement_0.75_2050")),
        parser_tree={},
    )
    monkeypatch.setattr(mkdocs_hooks, "get_documentation_context", lambda: context)
    result = mkdocs_hooks.on_page_content("<p>param::factor</p>")
    assert result == (
        "<p><a href='#param__regional.MAC.kappa_rel_abatement_0.75_2050'>"
        "<code>factor</code></a></p>"
    )
