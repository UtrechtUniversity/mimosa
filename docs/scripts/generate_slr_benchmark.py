"""Generate the AR6 comparison tables in the SLR documentation.

Run from the repository root with:

    python docs/scripts/generate_slr_benchmark.py
"""

from pathlib import Path
import sys

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from mimosa import MIMOSA, load_params  # noqa: E402
from mimosa.common import value  # noqa: E402
from mimosa.components import sealevelrise  # noqa: E402


OUTPUT_DIRECTORY = REPOSITORY_ROOT / "docs" / "assets" / "data"
TOTALS_OUTPUT = OUTPUT_DIRECTORY / "slr_ar6_benchmark.csv"
COMPONENTS_OUTPUT = OUTPUT_DIRECTORY / "slr_ar6_components.csv"

PROJECTIONS = ("low", "central", "high")
WARMING_LEVELS = (2.0, 3.0, 4.0)
INITIAL_TEMPERATURE = 1.27
FINAL_YEAR = 2100

# IPCC AR6 WGI Chapter 12, converted from a 1995--2014 to a 1900
# reference by adding the assessed 0.158 m historical rise.
AR6_WARMING_LEVEL_ESTIMATES = {
    2.0: (0.668, 0.558, 0.848),
    3.0: (0.778, 0.658, 0.968),
    4.0: (0.858, 0.738, 1.068),
}


def create_slr_model(projection):
    """Construct MIMOSA with one coherent SLR response parameter set."""

    params = load_params()
    params["model structure"]["sealevelrise options"]["projection"] = projection
    return MIMOSA(params, prerun=False).concrete_model


def run_temperature_benchmark(model, final_temperature):
    """Evaluate the SLR equations along a prescribed linear warming path."""

    initial_year = int(value(model.slr_initial_year))
    time_step = int(value(model.dt))

    thermal_fast = value(model.slr_thermal_fast_init)
    thermal_slow = value(model.slr_thermal_slow_init)
    glaciers = value(model.slr_gsic_init)
    greenland = value(model.slr_gis_init)
    antarctic_ocean_temperature = value(model.slr_ais_ocean_temp_init)
    antarctica = value(model.slr_ais_init)
    land_water = 0.0

    for year in range(initial_year + time_step, FINAL_YEAR + 1, time_step):
        forcing_year = year - time_step
        warming_fraction = (forcing_year - initial_year) / (
            FINAL_YEAR - initial_year
        )
        temperature = INITIAL_TEMPERATURE + warming_fraction * (
            final_temperature - INITIAL_TEMPERATURE
        )

        thermal_fast = value(
            sealevelrise.slr_thermal_expansion(
                thermal_fast,
                temperature,
                model.slr_thermal_fast_sensitivity,
                model.slr_thermal_fast_timescale,
                model,
            )
        )
        thermal_slow = value(
            sealevelrise.slr_thermal_expansion(
                thermal_slow,
                temperature,
                model.slr_thermal_slow_sensitivity,
                model.slr_thermal_slow_timescale,
                model,
            )
        )
        glaciers = value(sealevelrise.slr_gsic(glaciers, temperature, model))
        greenland = value(sealevelrise.slr_gis(greenland, temperature, model))
        antarctic_ocean_temperature = value(
            sealevelrise.slr_antarctic_ocean_temperature(
                antarctic_ocean_temperature,
                temperature,
                model,
            )
        )
        antarctica = value(
            sealevelrise.slr_ais(
                antarctica,
                antarctic_ocean_temperature,
                model,
            )
        )
        land_water += time_step * value(model.slr_lws_rate)

    components = {
        "Thermal expansion": thermal_fast + thermal_slow,
        "Glaciers": glaciers,
        "Greenland": greenland,
        "Antarctica": antarctica,
        "Land-water storage": land_water,
    }
    components["Total"] = sum(components.values())
    return components


def calculate_benchmark_tables():
    """Calculate the total and central-component AR6 comparison tables."""

    results = {}
    for projection in PROJECTIONS:
        model = create_slr_model(projection)
        results[projection] = {
            warming: run_temperature_benchmark(model, warming)
            for warming in WARMING_LEVELS
        }

    total_rows = []
    for warming in WARMING_LEVELS:
        median, likely_low, likely_high = AR6_WARMING_LEVEL_ESTIMATES[warming]
        total_rows.append(
            {
                "2100 warming": f"{warming:g} degrees C",
                "AR6 median [likely range]": (
                    f"{median:.3f} [{likely_low:.3f}--{likely_high:.3f}]"
                ),
                **{
                    projection: f"{results[projection][warming]['Total']:.3f}"
                    for projection in PROJECTIONS
                },
            }
        )

    component_rows = []
    for component in (
        "Thermal expansion",
        "Glaciers",
        "Greenland",
        "Antarctica",
        "Land-water storage",
    ):
        component_rows.append(
            {
                "Component": component,
                **{
                    f"{warming:g} degrees C": (
                        f"{results['central'][warming][component]:.3f}"
                    )
                    for warming in WARMING_LEVELS
                },
            }
        )

    return pd.DataFrame(total_rows), pd.DataFrame(component_rows)


def write_benchmark_tables():
    """Write the calculated benchmark tables to documentation CSV assets."""

    totals, components = calculate_benchmark_tables()
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    totals.to_csv(TOTALS_OUTPUT, index=False)
    components.to_csv(COMPONENTS_OUTPUT, index=False)
    return TOTALS_OUTPUT, COMPONENTS_OUTPUT


if __name__ == "__main__":
    for output_path in write_benchmark_tables():
        print(f"Wrote {output_path.relative_to(REPOSITORY_ROOT)}")
