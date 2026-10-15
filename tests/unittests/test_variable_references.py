"""Context resolution and stable links, independent of model construction."""

from dataclasses import replace

import pytest

from docs.scripts.variable_docs import VariableMetadata
from docs.scripts.variable_references import (
    group_variables,
    resolve_variable_reference,
    variable_anchor,
    variable_reference_url,
)


@pytest.fixture
def catalogue():
    coacch = VariableMetadata(
        name="damage_costs",
        description="COACCH damage and adaptation costs",
        unit="fraction_of_GDP",
        dimensions=("t", "regions"),
        context="coacch",
        has_declared_units=True,
    )
    accreu = replace(coacch, description="Residual ACCREU damages", context="accreu_sectoral")
    return (
        coacch,
        replace(coacch, context="coacch_noadaptation"),
        accreu,
        replace(accreu, name="adaptation_costs", description="Adaptation expenditure"),
    )


def test_groups_identical_entries_and_keeps_differing_variants(catalogue):
    entries = group_variables(catalogue)

    assert len(entries) == 3
    assert entries == group_variables(tuple(reversed(catalogue)))
    assert entries[0].metadata.name == "adaptation_costs"
    coacch = next(entry for entry in entries if entry.metadata.context == "coacch")
    assert coacch.contexts == ("coacch", "coacch_noadaptation")
    assert coacch.anchors == (
        "variable-coacch--damage_costs",
        "variable-coacch_noadaptation--damage_costs",
    )


@pytest.mark.parametrize(
    "change",
    [
        {"description": "Another description"},
        {"unit": "currency_unit"},
        {"dimensions": ("t",)},
        {"has_declared_units": False},
        {"requires_baseline": True},
    ],
)
def test_metadata_differences_are_not_merged(catalogue, change):
    original = catalogue[0]
    variant = replace(original, context="another_context", **change)

    assert len(group_variables((original, variant))) == 2


@pytest.mark.parametrize("kind", ["var", "varref"])
def test_page_context_resolves_both_marker_types(catalogue, kind):
    variable = resolve_variable_reference(
        f"{kind}::damage_costs", page_context="accreu_sectoral", catalogue=catalogue
    )

    assert variable.description == "Residual ACCREU damages"
    assert variable.context == "accreu_sectoral"


def test_explicit_context_overrides_page_context(catalogue):
    variable = resolve_variable_reference(
        "var::coacch_noadaptation::damage_costs",
        page_context="accreu_sectoral",
        catalogue=catalogue,
    )

    assert variable.description == "COACCH damage and adaptation costs"
    assert variable.context == "coacch_noadaptation"


def test_unqualified_identical_variants_resolve_deterministically(catalogue):
    variable = resolve_variable_reference("varref::damage_costs", catalogue=catalogue[:2])
    reversed_variable = resolve_variable_reference(
        "varref::damage_costs", catalogue=tuple(reversed(catalogue[:2]))
    )

    assert variable == reversed_variable == catalogue[0]


def test_unqualified_variable_unique_to_one_context_resolves(catalogue):
    variable = resolve_variable_reference("varref::adaptation_costs", catalogue=catalogue)

    assert variable.name == "adaptation_costs"
    assert variable.context == "accreu_sectoral"


def test_default_context_alias_matches_model_provider(catalogue):
    variable = resolve_variable_reference(
        "varref::damage_costs", page_context="default", catalogue=catalogue
    )

    assert variable.context == "coacch"


@pytest.mark.parametrize(
    "marker,context,expected",
    [
        ("var::missing", None, "Unknown variable 'missing'"),
        ("varref::missing::damage_costs", None, "Unknown variable context 'missing'"),
        ("var::damage_costs", "missing", "Unknown variable context 'missing'"),
        ("var::damage_costs", ["coacch"], "Unknown variable context"),
        ("var::adaptation_costs", "coacch", "unavailable in context 'coacch'"),
        ("varref::damage_costs", None, "Ambiguous variable 'damage_costs'"),
    ],
)
def test_reference_errors_identify_page_and_problem(catalogue, marker, context, expected):
    with pytest.raises(ValueError) as error:
        resolve_variable_reference(
            marker, page_context=context, page_path="components/damages/accreu.md",
            catalogue=catalogue,
        )

    assert str(error.value).startswith("components/damages/accreu.md: ")
    assert expected in str(error.value)


def test_ambiguity_error_explains_how_to_choose_context(catalogue):
    with pytest.raises(ValueError) as error:
        resolve_variable_reference("varref::damage_costs", catalogue=catalogue)

    assert "variable_context" in str(error.value)
    assert "varref::<context>::damage_costs" in str(error.value)
    assert "accreu_sectoral" in str(error.value)
    assert "coacch" in str(error.value)


@pytest.mark.parametrize(
    "marker", ["damage_costs", "param::damage_costs", "var::", "var::::damage_costs", "var::a::b::c"]
)
def test_malformed_markers_are_rejected(catalogue, marker):
    with pytest.raises(ValueError, match="Invalid variable reference"):
        resolve_variable_reference(marker, catalogue=catalogue)


def test_unknown_variable_does_not_fall_back_to_another_context(catalogue):
    with pytest.raises(ValueError, match="available contexts: accreu_sectoral"):
        resolve_variable_reference(
            "var::coacch::adaptation_costs", page_context="accreu_sectoral", catalogue=catalogue
        )


def test_context_anchors_survive_description_changes_and_regrouping(catalogue):
    before = {anchor for entry in group_variables(catalogue) for anchor in entry.anchors}
    changed = (replace(catalogue[0], description="Updated explanation"),) + catalogue[1:]
    after = {anchor for entry in group_variables(changed) for anchor in entry.anchors}

    assert after == before
    assert len(before) == len(catalogue)


@pytest.mark.parametrize(
    "source,target,expected",
    [
        ("", "variables/", "variables/"),
        ("components/damages/accreu/", "variables/", "../../../variables/"),
        ("components/index.html", "variables.html", "../variables.html"),
        ("components/damages/accreu.html", "variables.html", "../../variables.html"),
        ("index.html", "variables.html", "variables.html"),
        ("variables/", "variables/", ""),
        ("variables.html", "variables.html", ""),
    ],
)
def test_reference_urls_follow_page_depth_and_directory_url_setting(catalogue, source, target, expected):
    variable = catalogue[0]

    assert variable_reference_url(variable, source, target) == (
        f"{expected}#variable-coacch--damage_costs"
    )


def test_dotted_names_keep_distinct_anchors():
    assert variable_anchor("block.damage_costs", "coacch") == "variable-coacch--block.damage_costs"
    assert variable_anchor("block.damage_costs", "coacch") != variable_anchor("block_damage_costs", "coacch")


def test_resolver_uses_shared_catalogue_by_default(monkeypatch, catalogue):
    monkeypatch.setattr(
        "docs.scripts.variable_references.get_variable_catalogue", lambda: catalogue
    )

    assert resolve_variable_reference("var::coacch::damage_costs") == catalogue[0]
