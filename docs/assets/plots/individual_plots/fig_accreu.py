import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px

from .common import mimosa, model, COLORS, inputs, param_store


def p(var, region="World"):
    return param_store.getregional("ACCREU", var, region)


def create_all_figs():

    figs = {}

    ## Import raw ACCREU data
    raw = pd.read_excel("docs/assets/data/ACCREU_raw_data.xlsx", sheet_name=None)

    ## Global riverine plot
    figs["riverine_damages_global"] = fig_damages_global(
        raw["riverine_damages"], "riverine", mode="lines+markers"
    )
    figs["riverine_adaptation_global"] = fig_adaptation_global(
        raw["riverine_adaptation"], "riverine", groupvar="Adaptation level"
    )

    ## Global labour productivity plots
    figs["labourprod_damages_global"] = fig_labourprod_damages_global(raw)
    figs["labourprod_adaptation_global"] = fig_adaptation_global(
        raw["labourprod_adaptation"], "labourprod", maxval=2100
    )

    ## Global slr plot
    figs["slr_damages_global"] = fig_slr_damages_global(raw)
    figs["slr_adaptation_global"] = fig_adaptation_global(
        raw["slr_adaptation"], "slr", maxval=30
    )

    return figs


def fig_labourprod_damages_global(raw):
    fig = fig_damages_global(raw["labourprod_damages"], "labourprod", form="linear")
    fig_benefits = fig_damages_global(
        raw["labourprod_benefits"],
        "labourprod",
        form="linear",
        yvar="Benefits (% GDP)",
        yvar_param="benefit_cdd",
    )
    for trace in fig_benefits.data:
        fig.add_trace(trace)

    fig.add_annotation(x=3.4, y=0.03, text="Heat-related costs", showarrow=False)
    fig.add_annotation(x=3.7, y=-0.015, text="Cold-related benefits", showarrow=False)
    return fig


def fig_slr_damages_global(raw):
    fig = fig_damages_global(
        raw["slr_damages"],
        "slr",
        form="power",
        minval=0,
        maxval=0.5,
        xvar="global_slr_rel_to_2020",
    )
    fig.update_xaxes(ticksuffix=" m", title="SLR (relative to 2020)")
    return fig


def fig_damages_global(
    df,
    sector,
    form="quadratic",
    minval=1.2,
    maxval=4.5,
    mode="markers",
    xvar="Temperature",
    yvar="EAD (% GDP)",
    yvar_param="noadapt_ead",
):
    selection = df[df["Region"] == "World"]
    fig = make_subplots()
    for (rcp, subselection), color in zip(selection.groupby("RCP"), COLORS):
        fig.add_scatter(
            x=list(subselection[xvar]),
            y=list(subselection[yvar]),
            mode=mode,
            line_color=color,
            marker_color=color,
            name=rcp,
            showlegend=False,
        )
    # Add fit:
    x = np.linspace(minval, maxval)
    if form == "quadratic":
        a, b, c = (
            p(f"{sector}_{yvar_param}_constant"),
            p(f"{sector}_{yvar_param}_linear"),
            p(f"{sector}_{yvar_param}_quadr"),
        )
        y = a + b * x + c * x**2
    elif form == "linear":
        a, b = (
            p(f"{sector}_{yvar_param}_constant"),
            p(f"{sector}_{yvar_param}_linear"),
        )
        y = a + b * x
    elif form == "power":
        a, b, c = (
            p(f"{sector}_{yvar_param}_constant"),
            p(f"{sector}_{yvar_param}_prod"),
            p(f"{sector}_{yvar_param}_power"),
        )
        y = a + b * x**c
    else:
        raise ValueError(f"Unknown form {form}")
    fig.add_scatter(
        x=list(x),
        y=list(y),
        mode="lines",
        line={"color": "black", "dash": "dot"},
        name="Fit",
        showlegend=False,
    )

    fig.update_layout(
        margin={"l": 30, "r": 10, "b": 30, "t": 5}, height=250
    ).update_xaxes(ticksuffix=" °C").update_yaxes(title="% GDP", tickformat="p")

    return fig


def fig_adaptation_global(df, sector, maxval=700, groupvar="RCP"):
    selection = df[df["Region"] == "World"]
    fig = make_subplots()
    for (var, subselection), color in zip(
        selection.groupby(groupvar), COLORS if groupvar == "RCP" else COLORS[4:]
    ):
        fig.add_scatter(
            x=list(subselection["Cost (trillion USD)"] * 1000),
            y=list(subselection["Effectiveness"]),
            mode="markers",
            marker_color=color,
            name=f"{groupvar}: {var}",
            showlegend=False,
        )
    # Add fit:
    a, b = p(f"{sector}_adapt_eff_max_effectiveness"), p(
        f"{sector}_adapt_eff_cost_param"
    )
    x = np.linspace(0, maxval) / 1000
    y = a * (1 - np.exp(-b * x))
    fig.add_scatter(
        x=list(x * 1000),
        y=list(y),
        mode="lines",
        line={"color": "black", "dash": "dot"},
        name="Fit",
        showlegend=False,
    )

    fig.update_layout(
        margin={"l": 30, "r": 10, "b": 30, "t": 5}, height=250
    ).update_xaxes(
        title="Adaptation costs (billion USD)", rangemode="tozero"
    ).update_yaxes(
        title="Avoided damages", tickformat="p", rangemode="tozero"
    )
    return fig
