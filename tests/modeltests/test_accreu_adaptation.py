import numpy as np

from mimosa import MIMOSA, load_params


def test_literature_adaptation_calibration_matches_bcr_benchmarks():
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU adaptation"] = "separate"
    options["ACCREU_adaptation_calibration"] = "literature"
    options["ACCREU_adaptation_impose_optimal"] = True

    model = MIMOSA(params, prerun=False)
    simulation = model.run_simulation()

    years = np.asarray([simulation.year(t) for t in simulation.t])
    through_2100 = years <= 2100
    period_length = simulation.period_length.values[through_2100]
    discount_factor = 1 / 1.05 ** (years[through_2100] - years[0])

    bcrs = {}
    for sector in ["labourprod", "riverine", "slr"]:
        costs = getattr(simulation, f"{sector}_adaptation_costs_abs").values[
            through_2100
        ]
        gross_damages = (
            getattr(simulation, f"{sector}_damage_costs_gross").values
            * simulation.GDP_gross.values
        )[through_2100]
        effectiveness = getattr(
            simulation, f"{sector}_avoided_damages_adapt"
        ).values[through_2100]
        weights = period_length[:, None] * discount_factor[:, None]
        bcrs[sector] = np.sum(gross_damages * effectiveness * weights) / np.sum(
            costs * weights
        )

    assert 2.2 < bcrs["labourprod"] < 2.6
    assert 4.0 < bcrs["riverine"] < 5.2
    assert 7.0 < bcrs["slr"] < 8.5
