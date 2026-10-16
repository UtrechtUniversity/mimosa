"""Options live beside the scientific assumptions they control."""

import pytest

from mimosa import load_params
from mimosa.common.config.parseconfig import check_params


def test_option_defaults_and_module_selectors_are_preserved():
    params = load_params()
    accreu = params["economics"]["damages"]["accreu"]
    assert accreu["adaptation"] == "noadaptation"
    assert accreu["cba_strategy"] == "mitigation_then_adaptation"
    assert accreu["adaptation_determination"] == "analytical_optimum"
    assert accreu["adaptation_calibration"] == "accreu"
    assert accreu["monetise_mortality"] is True
    assert accreu["mortality_svl_rel_gdp_cap"] == 117.59
    assert params["sealevelrise"]["projection"] == "central"
    assert set(params["model structure"]) == {
        "damage module",
        "emissiontrade module",
        "financialtransfer module",
        "effortsharing module",
        "welfare module",
        "objective module",
    }


@pytest.mark.parametrize(
    "option, values",
    [
        ("adaptation", ["sectoral", "combined", "noadaptation"]),
        ("cba_strategy", ["joint", "mitigation_then_adaptation"]),
        ("adaptation_determination", ["solver_control", "analytical_optimum"]),
        (
            "adaptation_calibration",
            ["accreu", "literature_low", "literature", "literature_high"],
        ),
        ("monetise_mortality", [False, True]),
    ],
)
def test_moved_options_accept_existing_values_and_reject_invalid_values(option, values):
    for value in values:
        result = check_params({"economics": {"damages": {"accreu": {option: value}}}})
        assert result["economics"]["damages"]["accreu"][option] == value
    with pytest.raises(ValueError):
        check_params({"economics": {"damages": {"accreu": {option: "invalid"}}}})


@pytest.mark.parametrize("projection", ["low", "central", "high"])
def test_projection_accepts_existing_choices(projection):
    assert (
        check_params({"sealevelrise": {"projection": projection}})["sealevelrise"][
            "projection"
        ]
        == projection
    )


def test_old_separate_adaptation_name_is_rejected():
    with pytest.raises(ValueError):
        check_params({"economics": {"damages": {"accreu": {"adaptation": "separate"}}}})


@pytest.mark.parametrize(
    "legacy",
    [
        {
            "model structure": {
                "damage module options": {"ACCREU_adaptation": "sectoral"}
            }
        },
        {"model structure": {"damage module options": {}}},
        {"model structure": {"sealevelrise options": {"projection": "central"}}},
        {"model structure": {"sealevelrise options": {}}},
        {"economics": {"damages": {"accreu": {"ACCREU_adaptation": "sectoral"}}}},
    ],
)
def test_legacy_option_paths_are_rejected_instead_of_silently_ignored(legacy):
    with pytest.raises(RuntimeWarning, match="obsolete or misspelled"):
        check_params(legacy)
