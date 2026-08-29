"""Calculate global benefit-cost ratios for ACCREU adaptation.

Run from the repository root with:

    python diagnostics/adaptation_bcr.py
"""

from copy import deepcopy
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from mimosa import MIMOSA, load_params  # noqa: E402

DISCOUNTING = "fixed"  # "fixed" or "ramsey"
DISCOUNT_RATE = 0.05
FINAL_YEAR = 2100

CALIBRATIONS = (
    "accreu",
    "literature_low",
    "literature",
    "literature_high",
)

SECTORS = {
    "separate": {
        "Labour productivity": (
            "labourprod_damage_costs_gross",
            "labourprod_avoided_damages_adapt",
            "labourprod_adaptation_costs_abs",
        ),
        "Riverine flooding": (
            "riverine_damage_costs_gross",
            "riverine_avoided_damages_adapt",
            "riverine_adaptation_costs_abs",
        ),
        "SLR": (
            "slr_damage_costs_gross",
            "slr_avoided_damages_adapt",
            "slr_adaptation_costs_abs",
        ),
    },
    "combined": {
        "Combined labour and riverine": (
            "combined_labprod_riv_damage_costs_gross",
            "combined_labprod_riv_avoided_damages_adapt",
            "combined_labprod_riv_adaptation_costs_abs",
        ),
        "SLR": (
            "slr_damage_costs_gross",
            "slr_avoided_damages_adapt",
            "slr_adaptation_costs_abs",
        ),
    },
}

OUTPUT_DIRECTORY = REPOSITORY_ROOT / "output"
TABLE_OUTPUT = OUTPUT_DIRECTORY / "adaptation_bcr.csv"
PLOT_OUTPUT = OUTPUT_DIRECTORY / "adaptation_bcr.html"

BENEFITS_COLUMN = "avoided damages (trillion USD2010)"
COSTS_COLUMN = "adaptation costs (trillion USD2010)"
NET_BENEFITS_COLUMN = "net benefits (trillion USD2010)"


def accreu_params(adaptation_type, calibration="accreu"):
    """Load a no-mitigation ACCREU analytical-adaptation scenario."""

    params = load_params()
    params["economics"]["damages"]["ignore damages"] = False
    params["model structure"]["damage module"] = "ACCREU"
    options = params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = adaptation_type
    options["ACCREU_adaptation_calibration"] = calibration
    options["ACCREU_adaptation_determination"] = "analytical_optimum"
    options["ACCREU_CBA_strategy"] = "joint"
    return params


def no_adaptation_reference(params):
    """Run the unadapted pathway used only for Ramsey discount factors."""

    reference_params = deepcopy(params)
    options = reference_params["model structure"]["damage module options"]
    options["ACCREU_adaptation"] = "noadaptation"
    options["ACCREU_adaptation_determination"] = "solver_control"
    return MIMOSA(reference_params, prerun=False).run_simulation()


def discount_factors(simulation, params, ramsey_reference=None):
    """Return fixed or Ramsey discount factors from the first model year."""

    years = np.asarray([simulation.year(t) for t in simulation.t], dtype=float)
    if DISCOUNTING == "fixed":
        return 1 / (1 + DISCOUNT_RATE) ** (years - years[0])
    if DISCOUNTING != "ramsey":
        raise ValueError("DISCOUNTING must be 'fixed' or 'ramsey'.")
    if ramsey_reference is None:
        raise ValueError("Ramsey discounting requires an unadapted reference run.")

    consumption_per_capita = np.asarray(
        [
            sum(ramsey_reference.consumption[t, r] for r in simulation.regions)
            / sum(ramsey_reference.population[t, r] for r in simulation.regions)
            for t in simulation.t
        ]
    )
    prtp = params["economics"]["PRTP"]
    elasmu = params["economics"]["elasmu"]
    return np.exp(-prtp * (years - years[0])) * (
        consumption_per_capita / consumption_per_capita[0]
    ) ** (-elasmu)


def sector_bcr(simulation, weights, variable_names):
    """Calculate discounted benefits, costs, net benefits and average BCR."""

    gross_name, effectiveness_name, costs_name = variable_names
    gross_damages = getattr(simulation, gross_name)
    effectiveness = getattr(simulation, effectiveness_name)
    adaptation_costs = getattr(simulation, costs_name)

    avoided_damages = np.asarray(
        [
            sum(
                gross_damages[t, r]
                * simulation.GDP_gross[t, r]
                * effectiveness[t, r]
                for r in simulation.regions
            )
            for t in simulation.t
        ]
    )
    costs = np.asarray(
        [
            sum(adaptation_costs[t, r] for r in simulation.regions)
            for t in simulation.t
        ]
    )
    benefits_pv = np.sum(avoided_damages * weights)
    costs_pv = np.sum(costs * weights)
    return {
        BENEFITS_COLUMN: benefits_pv,
        COSTS_COLUMN: costs_pv,
        NET_BENEFITS_COLUMN: benefits_pv - costs_pv,
        "BCR": benefits_pv / costs_pv,
    }


def calculate_bcrs():
    """Calculate the global BCR table for all adaptation configurations."""

    rows = []
    ramsey_reference = (
        no_adaptation_reference(accreu_params("separate"))
        if DISCOUNTING == "ramsey"
        else None
    )
    for adaptation_type, sectors in SECTORS.items():
        for calibration in CALIBRATIONS:
            params = accreu_params(adaptation_type, calibration)
            simulation = MIMOSA(params, prerun=False).run_simulation()

            years = np.asarray([simulation.year(t) for t in simulation.t], dtype=float)
            through_final_year = years <= FINAL_YEAR
            period_lengths = np.asarray(
                [simulation.period_length[t] for t in simulation.t]
            )
            weights = (
                period_lengths
                * discount_factors(simulation, params, ramsey_reference)
                * through_final_year
            )

            sector_results = []
            for sector, variable_names in sectors.items():
                result = sector_bcr(simulation, weights, variable_names)
                sector_results.append(result)
                rows.append(
                    {
                        "adaptation type": adaptation_type,
                        "calibration": calibration,
                        "sector": sector,
                        **result,
                    }
                )

            total_benefits = sum(
                result[BENEFITS_COLUMN] for result in sector_results
            )
            total_costs = sum(
                result[COSTS_COLUMN] for result in sector_results
            )
            rows.append(
                {
                    "adaptation type": adaptation_type,
                    "calibration": calibration,
                    "sector": "Total",
                    BENEFITS_COLUMN: total_benefits,
                    COSTS_COLUMN: total_costs,
                    NET_BENEFITS_COLUMN: total_benefits - total_costs,
                    "BCR": total_benefits / total_costs,
                }
            )
    return pd.DataFrame(rows)


def create_figure(results):
    """Create grouped BCR bars for separate and combined adaptation."""

    discounting_label = (
        f"{DISCOUNT_RATE:.0%} fixed discounting"
        if DISCOUNTING == "fixed"
        else "Ramsey discounting"
    )
    figure = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Separate adaptation", "Combined adaptation"),
    )
    colors = ("#636EFA", "#EF553B", "#00CC96", "#AB63FA")
    for column, adaptation_type in enumerate(SECTORS, start=1):
        subset = results[results["adaptation type"] == adaptation_type]
        for calibration, color in zip(CALIBRATIONS, colors):
            calibration_results = subset[subset["calibration"] == calibration]
            figure.add_trace(
                go.Bar(
                    x=calibration_results["sector"],
                    y=calibration_results["BCR"],
                    name=calibration,
                    legendgroup=calibration,
                    showlegend=column == 1,
                    marker_color=color,
                    hovertemplate="%{x}<br>BCR=%{y:.2f}<extra>%{fullData.name}</extra>",
                ),
                row=1,
                col=column,
            )
        figure.add_hline(y=1, line_dash="dash", line_color="black", row=1, col=column)

    figure.update_yaxes(title_text="Benefit-cost ratio", rangemode="tozero")
    figure.update_layout(
        title=(
            f"Global ACCREU adaptation BCRs through {FINAL_YEAR} "
            f"({discounting_label})"
        ),
        barmode="group",
        template="plotly_white",
    )
    return figure


if __name__ == "__main__":
    bcrs = calculate_bcrs()
    print(bcrs.to_string(index=False, float_format=lambda value: f"{value:.3f}"))

    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    bcrs.to_csv(TABLE_OUTPUT, index=False)
    create_figure(bcrs).write_html(PLOT_OUTPUT)
    print(f"Wrote {TABLE_OUTPUT.relative_to(REPOSITORY_ROOT)}")
    print(f"Wrote {PLOT_OUTPUT.relative_to(REPOSITORY_ROOT)}")
