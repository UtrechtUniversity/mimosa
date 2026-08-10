import pytest

from mimosa import MIMOSA, load_params


pytestmark = pytest.mark.simulation


def run_slr_projection(projection):
    params = load_params()
    params["model structure"]["sealevelrise options"]["projection"] = projection
    model = MIMOSA(params, prerun=False)
    return model.run_simulation()


def test_default_slr_projection_is_central():
    params = load_params()

    assert (
        params["model structure"]["sealevelrise options"]["projection"]
        == "central"
    )


def test_invalid_slr_projection_is_rejected_by_configuration():
    params = load_params()
    params["model structure"]["sealevelrise options"]["projection"] = "invalid"

    with pytest.raises(ValueError, match="not in allowed values"):
        MIMOSA(params, prerun=False)


def test_slr_projection_sets_share_initial_state_and_diverge():
    simulations = {
        projection: run_slr_projection(projection)
        for projection in ("low", "central", "high")
    }

    initial_values = [simulation.total_SLR[0] for simulation in simulations.values()]
    assert initial_values == pytest.approx([0.23, 0.23, 0.23])

    slr_2100 = [
        simulations[projection].total_SLR[15]
        for projection in ("low", "central", "high")
    ]
    assert slr_2100[0] < slr_2100[1] < slr_2100[2]

    assert all(
        simulation.slr_cumlws[15] == pytest.approx(0.03)
        for simulation in simulations.values()
    )
