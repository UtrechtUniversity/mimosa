import pytest

from mimosa.components import sealevelrise


class MockAbstractModel:
    beginyear = 2025
    slr_reference_year = 1900
    slr_initial_year = 2025

    slr_gsic_total_ice = 0.32
    slr_gsic_temp_sensitivity = 2.0
    slr_gsic_timescale = 200.0

    slr_gis_total_ice = 7.3
    slr_gis_threshold = 1.8
    slr_gis_transition_width = 0.6
    slr_gis_base_timescale = 6000.0
    slr_gis_timescale_sensitivity = 0.3

    slr_ais_ocean_temp_scaling = 0.60
    slr_ais_ocean_temp_timescale = 30.0
    slr_ais_total_ice = 5.0
    slr_ais_background_rate = 0.0008
    slr_ais_temp_sensitivity = 0.0002
    slr_ais_fast_rate = 0.005
    slr_ais_fast_threshold = 2.5
    slr_ais_fast_transition_width = 0.15


@pytest.fixture
def m():
    return MockAbstractModel()


def test_initial_values_share_1900_reference(m):
    assert sealevelrise.slr_initial_value(0.08, m) == pytest.approx(0.08)

    m.beginyear = 1900
    assert sealevelrise.slr_initial_value(0.08, m) == pytest.approx(0.0)


def test_projection_parameter_sets_have_identical_structure():
    parameter_sets = sealevelrise.SLR_PROJECTION_PARAMETER_SETS
    central_keys = set(parameter_sets["central"])

    assert set(parameter_sets) == {"low", "central", "high"}
    assert all(set(values) == central_keys for values in parameter_sets.values())


def test_relaxation_is_time_step_invariant_for_constant_forcing(m):
    initial = 0.05
    equilibrium = 0.5
    timescale = 100.0

    one_step = sealevelrise.relax_to_equilibrium(
        initial, equilibrium, timescale, 10
    )

    ten_steps = initial
    for _ in range(10):
        ten_steps = sealevelrise.relax_to_equilibrium(
            ten_steps, equilibrium, timescale, 1
        )

    assert ten_steps == pytest.approx(one_step)


def test_glacier_equilibrium_is_temperature_dependent_and_bounded(m):
    cold = sealevelrise.slr_gsic_equilibrium(1.0, m)
    warm = sealevelrise.slr_gsic_equilibrium(3.0, m)

    assert 0 < cold < warm < m.slr_gsic_total_ice


def test_greenland_equilibrium_and_timescale_respond_to_warming(m):
    assert sealevelrise.slr_gis_equilibrium(0.0, m) == pytest.approx(0.0)

    equilibrium_cold = sealevelrise.slr_gis_equilibrium(1.0, m)
    equilibrium_warm = sealevelrise.slr_gis_equilibrium(3.0, m)
    timescale_cold = sealevelrise.slr_gis_timescale(1.0, m)
    timescale_warm = sealevelrise.slr_gis_timescale(3.0, m)

    assert 0 < equilibrium_cold < equilibrium_warm < m.slr_gis_total_ice
    assert timescale_warm < timescale_cold


def test_antarctic_fast_response_activates_smoothly(m):
    rate_below_threshold = sealevelrise.slr_ais_rate(1.0, m)
    rate_above_threshold = sealevelrise.slr_ais_rate(4.0, m)

    assert rate_above_threshold > rate_below_threshold
    assert rate_below_threshold > 0


def test_antarctic_update_is_limited_by_remaining_ice(m):
    ocean_temperature = 4.0
    contribution_small = (
        sealevelrise.slr_ais(0.1, ocean_temperature, m, 5) - 0.1
    )
    contribution_large = (
        sealevelrise.slr_ais(4.9, ocean_temperature, m, 5) - 4.9
    )

    assert contribution_large < contribution_small
    assert contribution_large > 0


def test_projection_sets_order_ordinary_responses():
    parameter_sets = sealevelrise.SLR_PROJECTION_PARAMETER_SETS

    assert parameter_sets["low"]["thermal_fast_sensitivity"] < parameter_sets[
        "central"
    ]["thermal_fast_sensitivity"]
    assert parameter_sets["low"]["gsic_timescale"] > parameter_sets["central"][
        "gsic_timescale"
    ]
    assert parameter_sets["low"]["ais_background_rate"] < parameter_sets[
        "central"
    ]["ais_background_rate"]
