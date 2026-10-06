import pytest

from mimosa import load_params
from mimosa.common.config.parseconfig import check_params


def test_custom_constraints_retains_only_supported_options():
    assert set(load_params()["custom_constraints"]) == {
        "constraint_variables", "disabled_constraints"
    }


@pytest.mark.parametrize(
    "mapping",
    [None, {}, {"alpha": {None: 0.35}}, {"relative_abatement": {(1, "CAN"): 0.2}}],
)
def test_removed_custom_mapping_is_rejected_as_obsolete(mapping):
    with pytest.raises(RuntimeWarning, match="custom_constraints - custom_mapping"):
        check_params({"custom_constraints": {"custom_mapping": mapping}})


def test_trajectory_and_deactivation_configuration_remain_supported():
    custom = {
        "constraint_variables": {"relative_abatement": 0.2},
        "disabled_constraints": ["carbon_budget"],
    }
    assert check_params({"custom_constraints": custom})["custom_constraints"] == custom
