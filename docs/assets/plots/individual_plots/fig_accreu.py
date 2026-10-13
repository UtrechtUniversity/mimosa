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

    ## Create global riverine plot
    figs["riverine_damages_global"] = fig_riverine_damages_global(
        raw["riverine_damages"]
    )
    figs["riverine_adaptation_global"] = fig_riverine_adaptation_global(
        raw["riverine_adaptation"]
    )

    return figs


def fig_riverine_damages_global(df):
    selection = df[df["Region"] == "World"]
    fig = make_subplots()
    for (rcp, subselection), color in zip(selection.groupby("RCP"), COLORS):
        fig.add_scatter(
            x=list(subselection["Temperature"]),
            y=list(subselection["EAD (% GDP)"]),
            mode="lines+markers",
            line_color=color,
            name=rcp,
            showlegend=False,
        )
    # Add fit:
    a, b, c = (
        p("riverine_noadapt_ead_constant"),
        p("riverine_noadapt_ead_linear"),
        p("riverine_noadapt_ead_quadr"),
    )
    x = np.linspace(1.2, 4.5)
    y = a + b * x + c * x**2
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


def fig_riverine_adaptation_global(df):
    selection = df[df["Region"] == "World"]
    fig = make_subplots()
    for (level, subselection), color in zip(
        selection.groupby("Adaptation level"), COLORS[4:]
    ):
        fig.add_scatter(
            x=list(subselection["Cost (trillion USD)"] * 1000),
            y=list(subselection["Effectiveness"]),
            mode="markers",
            marker_color=color,
            name=f"Adaptation level: {level}",
            showlegend=False,
        )
    # Add fit:
    a, b = p("riverine_adapt_eff_max_effectiveness"), p("riverine_adapt_eff_cost_param")
    x = np.linspace(0, 700) / 1000
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
