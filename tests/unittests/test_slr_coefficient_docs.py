"""SLR documentation tables stay aligned with the component coefficients."""

from types import SimpleNamespace
from xml.etree import ElementTree
import re

import pytest
from pyomo.environ import ConcreteModel, Param, value

from docs.scripts.slr_coefficient_docs import (
    SLR_COEFFICIENT_GROUPS,
    render_slr_coefficients,
)
from mimosa.components import sealevelrise


@pytest.fixture(scope="module")
def slr_model():
    # Only construct this component: no simulation, solver or extra documentation
    # contexts are needed to inspect its initialized scalar parameters.
    model = ConcreteModel()
    model.t = [0, 1]
    model.period_length = {0: 0, 1: 5}
    model.beginyear = 2025
    model.temperature = {0: 1.27, 1: 1.3}
    inputs = SimpleNamespace(config_value=lambda path: "central")
    sealevelrise.get_constraints(model, inputs)
    return model


def rendered_block(source):
    markdown = pytest.importorskip("markdown", reason="Rendering tests require .[docs]")
    pytest.importorskip("pymdownx.details", reason="Rendering tests require .[docs]")
    html = markdown.markdown(
        source, extensions=["admonition", "pymdownx.details", "md_in_html", "tables"]
    )
    return ElementTree.fromstring(f"<root>{html}</root>").find("details")


def rows(table):
    return [["".join(cell.itertext()) for cell in row] for row in table.findall(".//tr")]


def test_every_slr_parameter_is_documented_once(slr_model):
    names = [entry[0] for group in SLR_COEFFICIENT_GROUPS.values() for entry in group]
    actual = {param.name for param in slr_model.component_objects(Param)}
    assert len(names) == len(set(names))
    assert set(names) == actual
    projection_keys = {
        name[len("slr_"):] for name in names
        if name[len("slr_"):] in sealevelrise.SLR_PROJECTION_PARAMETER_SETS["central"]
    }
    assert projection_keys == set(sealevelrise.SLR_PROJECTION_PARAMETER_SETS["central"])


def test_thermal_table_uses_all_three_projection_sets(slr_model, monkeypatch):
    monkeypatch.setitem(sealevelrise.SLR_PROJECTION_PARAMETER_SETS["low"], "thermal_fast_timescale", 43.25)
    block = rendered_block(render_slr_coefficients("thermal", slr_model))
    assert "open" not in block.attrib
    table = rows(block.find(".//table"))
    assert table[0] == ["Symbol", "Meaning", "Units", "Low", "Central (default)", "High"]
    assert table[3][-3:] == ["43.25", "40", "30"]
    assert len(table) == 5


def test_initial_values_are_read_from_the_model(slr_model):
    block = rendered_block(render_slr_coefficients("initial", slr_model))
    table = rows(block.find(".//table"))
    assert block.findtext("summary") == "Reference years and initial values"
    assert table[0] == ["Symbol", "Meaning", "Units", "Value"]
    assert len(table) == 9
    assert [row[-1] for row in table[1:]] == [
        format(value(getattr(slr_model, name)), ".6g")
        for name, *_ in SLR_COEFFICIENT_GROUPS["initial"]
    ]
    # A different initialized value must appear without editing the renderer.
    replacement = SimpleNamespace(**{
        name: 0.123 if name == "slr_thermal_fast_init" else value(getattr(slr_model, name))
        for name, *_ in SLR_COEFFICIENT_GROUPS["initial"]
    })
    assert rows(rendered_block(render_slr_coefficients("initial", replacement)).find(".//table"))[3][-1] == "0.123"


def test_shared_constants_and_varying_coefficients_have_separate_tables(slr_model):
    block = rendered_block(render_slr_coefficients("glaciers", slr_model))
    varying, fixed = [rows(table) for table in block.findall(".//table")]
    assert len(varying) == 3
    assert len(fixed) == 2
    assert fixed[1] == [r"$P_{\mathrm{GL}}$", "Glacier sea-level potential", "m", "0.32"]
    assert all(len(row) == 6 for row in varying)
    assert all(len(row) == 4 for row in fixed)


def test_land_water_has_one_shared_value(slr_model):
    block = rendered_block(render_slr_coefficients("land_water", slr_model))
    assert len(block.findall(".//table")) == 1
    assert rows(block.find(".//table"))[1][-1] == "0.0004"


def test_slr_equation_links_resolve_to_local_rows_without_markdown(slr_model):
    source = "\n".join(
        render_slr_coefficients(section, slr_model)
        for section in SLR_COEFFICIENT_GROUPS
    )
    anchors = re.findall(
        r'<span id="slrcoef__([^"]+)"[^>]+data-slr-coefficients="([^"]+)">',
        source,
    )
    assert len(anchors) == len(dict(anchors))
    targets = set(re.findall(r"\\href\{\./#slrcoef__([^}]+)\}", sealevelrise.get_constraints.__doc__))
    names = {
        name for section, group in SLR_COEFFICIENT_GROUPS.items()
        if section != "initial" for name, *_ in group
    }
    assert targets == names
    lookup = dict(anchors)
    for target in targets:
        assert lookup[target] == target


def test_thermal_equations_link_each_box_to_its_own_variables_and_coefficients():
    thermal = sealevelrise.get_constraints.__doc__.split("# Thermal expansion")[1].split("# Glaciers")[0]
    equations = re.findall(r"\$\$(.*?)\$\$", thermal, re.DOTALL)
    assert len(equations) == 3
    for box, equation in zip(("fast", "slow"), equations):
        assert set(re.findall(r"\\href\{\./#var__([^}]+)\}", equation)) == {
            f"slr_thermal_{box}", "temperature",
        }
        assert set(re.findall(r"\\href\{\./#slrcoef__([^}]+)\}", equation)) == {
            f"slr_thermal_{box}_sensitivity", f"slr_thermal_{box}_timescale",
        }
        assert rf"\text{{SLR}}_{{\mathrm{{thermal,{box}}},t}}" in equation
        assert rf"\text{{SLR}}_{{\mathrm{{thermal,{box}}},t-1}}" in equation
    assert re.findall(r"\\href\{\./#var__([^}]+)\}", equations[2]) == [
        "slr_thermal", "slr_thermal_fast", "slr_thermal_slow",
    ]
