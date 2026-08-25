import numpy as np
import pytest

from mimosa import MIMOSA, load_params


@pytest.mark.parametrize(
    ("calibration", "bcr_ranges"),
    [
        (
            "literature_low",
            {"labourprod": (1.8, 2.2), "riverine": (1.8, 2.5), "slr": (4.0, 5.5)},
        ),
        (
            "literature",
            {"labourprod": (2.2, 2.6), "riverine": (4.0, 5.2), "slr": (7.0, 8.5)},
        ),
        (
            "literature_high",
            {
                "labourprod": (3.3, 4.1),
                "riverine": (6.2, 7.5),
                "slr": (12.5, 15.5),
            },
        ),
    ],
)
def test_literature_adaptation_calibration_matches_bcr_benchmarks(
    calibration, bcr_ranges
):
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "separate"
    options["ACCREU_adaptation_calibration"] = calibration
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
        effectiveness = getattr(simulation, f"{sector}_avoided_damages_adapt").values[
            through_2100
        ]
        weights = period_length[:, None] * discount_factor[:, None]
        bcrs[sector] = np.sum(gross_damages * effectiveness * weights) / np.sum(
            costs * weights
        )

    for sector, bcr_range in bcr_ranges.items():
        assert bcr_range[0] < bcrs[sector] < bcr_range[1]


@pytest.mark.parametrize(
    ("calibration", "bcr_range"),
    [
        ("literature_low", (2.3, 2.6)),
        ("literature", (4.1, 4.5)),
        ("literature_high", (8.4, 9.2)),
    ],
)
def test_combined_literature_calibration_matches_bcr_benchmarks(calibration, bcr_range):
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "combined"
    options["ACCREU_adaptation_calibration"] = calibration
    options["ACCREU_adaptation_impose_optimal"] = True

    simulation = MIMOSA(params, prerun=False).run_simulation()

    years = np.asarray([simulation.year(t) for t in simulation.t])
    through_2100 = years <= 2100
    period_length = simulation.period_length.values[through_2100]
    discount_factor = 1 / 1.05 ** (years[through_2100] - years[0])
    weights = period_length[:, None] * discount_factor[:, None]

    costs = simulation.combined_labprod_riv_adaptation_costs_abs.values[through_2100]
    gross_damages = (
        simulation.combined_labprod_riv_damage_costs_gross.values
        * simulation.GDP_gross.values
    )[through_2100]
    effectiveness = simulation.combined_labprod_riv_avoided_damages_adapt.values[
        through_2100
    ]
    bcr = np.sum(gross_damages * effectiveness * weights) / np.sum(costs * weights)

    assert bcr_range[0] < bcr < bcr_range[1]
