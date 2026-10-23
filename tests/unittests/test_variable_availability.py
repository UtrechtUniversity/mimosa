"""Availability uses public settings and ignores unrelated context differences."""

import pytest

from docs.scripts.variable_availability import availability_requirements
from mimosa.common.config.parseconfig import check_params


@pytest.fixture
def context_params():
    overrides = {
        "baseline": {},
        "trade": {"model structure": {"emissiontrade module": "emissiontrade"}},
        "equal_mitigation": {
            "model structure": {
                "emissiontrade module": "emissiontrade",
                "effortsharing module": "equal_mitigation_costs",
                "welfare module": "cost_minimising",
            }
        },
        "equal_total": {
            "model structure": {
                "emissiontrade module": "emissiontrade",
                "effortsharing module": "equal_total_costs",
                "welfare module": "cost_minimising",
            }
        },
        "ability_to_pay": {
            "model structure": {
                "emissiontrade module": "emissiontrade",
                "effortsharing module": "ability_to_pay",
                "welfare module": "cost_minimising",
            }
        },
        "accreu_noadaptation": {
            "model structure": {"damage module": "ACCREU"},
            "economics": {"damages": {"accreu": {"adaptation": "noadaptation"}}},
        },
        "accreu_sectoral": {
            "model structure": {"damage module": "ACCREU"},
            "economics": {"damages": {"accreu": {"adaptation": "sectoral"}}},
        },
        "accreu_no_mortality": {
            "model structure": {"damage module": "ACCREU"},
            "economics": {"damages": {"accreu": {
                "adaptation": "sectoral", "monetise_mortality": False,
            }}},
        },
        "accreu_combined": {
            "model structure": {"damage module": "ACCREU"},
            "economics": {"damages": {"accreu": {"adaptation": "combined"}}},
        },
    }
    return {name: check_params(config) for name, config in overrides.items()}


def test_trading_variables_require_only_emissiontrade(context_params):
    requirements = availability_requirements(
        {"trade", "equal_mitigation", "equal_total", "ability_to_pay"}, context_params
    )

    assert requirements == ((("model structure.emissiontrade module", ("emissiontrade",)),),)


def test_common_effort_level_requires_either_effortsharing_value(context_params):
    requirements = availability_requirements({"equal_mitigation", "equal_total"}, context_params)

    assert requirements == (((
        "model structure.effortsharing module", ("equal_mitigation_costs", "equal_total_costs")
    ),),)


def test_gross_accreu_damages_require_adaptation_but_not_mortality(context_params):
    requirements = availability_requirements(
        {"accreu_sectoral", "accreu_no_mortality", "accreu_combined"}, context_params
    )

    assert requirements == ((
        ("model structure.damage module", ("ACCREU",)),
        ("economics.damages.accreu.adaptation", ("combined", "sectoral")),
    ),)


def test_physical_mortality_requires_only_accreu(context_params):
    requirements = availability_requirements(
        {"accreu_noadaptation", "accreu_sectoral", "accreu_no_mortality", "accreu_combined"},
        context_params,
    )

    assert requirements == ((("model structure.damage module", ("ACCREU",)),),)


def test_monetary_mortality_requires_accreu_and_monetisation(context_params):
    requirements = availability_requirements(
        {"accreu_noadaptation", "accreu_sectoral", "accreu_combined"}, context_params
    )

    assert requirements == ((
        ("model structure.damage module", ("ACCREU",)),
        ("economics.damages.accreu.monetise_mortality", (True,)),
    ),)


def test_universal_variables_have_no_requirements(context_params):
    assert availability_requirements(set(context_params), context_params) == ()


def test_context_names_do_not_affect_requirements(context_params):
    renamed = {f"internal_{index}": params for index, params in enumerate(context_params.values())}
    positive = {name for name, params in renamed.items()
                if params["model structure"]["emissiontrade module"] == "emissiontrade"}

    assert availability_requirements(positive, renamed) == (
        (("model structure.emissiontrade module", ("emissiontrade",)),),
    )
