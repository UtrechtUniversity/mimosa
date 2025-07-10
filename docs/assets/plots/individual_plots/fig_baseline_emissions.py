import json
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from .common import mimosa, model, COLORS, params


def create_fig():

    ## Baseline emissions
    data = pd.read_csv("mimosa/inputdata/data/data_IMAGE_SSP_harmonised_2020.csv")
    data_emissions = (
        data.drop(columns=["Model", "Unit"])
        .set_index(["Scenario", "Region", "Variable"])
        .rename_axis("Year", axis=1)
        .stack()
    )
    data_emissions = (
        data_emissions.unstack("Variable").reset_index().astype({"Year": int})
    )
    data_emissions["Emissions|CO2"] /= 1000
    data_emissions["Scenario"] = data_emissions["Scenario"].str.split("-").str[0]

    _fig_baseline_emissions = px.line(
        data_emissions[data_emissions["Year"] >= 2020],
        x="Year",
        y="Emissions|CO2",
        facet_col="Region",
        facet_col_wrap=13,
        facet_col_spacing=0.005,
        color="Scenario",
        width=1200,
        render_mode="svg",
    )

    fig_baseline_emissions = make_subplots()
    for trace in _fig_baseline_emissions.data:
        fig_baseline_emissions.add_scatter(
            x=trace.x.tolist(),
            y=trace.y.tolist(),
            name=trace.name,
            mode=trace.mode,
            line=trace.line,
            legendgroup=trace.legendgroup,
            showlegend=trace.showlegend,
            xaxis=trace.xaxis,
            yaxis=trace.yaxis,
            hovertemplate=trace.hovertemplate,
        )

    fig_baseline_emissions.layout = _fig_baseline_emissions.layout

    fig_baseline_emissions.update_layout(
        legend={"orientation": "h", "x": 0.5, "xanchor": "center"},
        margin={"r": 30, "t": 30, "l": 50},
    )
    (
        fig_baseline_emissions.update_xaxes(title=None, range=[2021, 2100])
        .update_yaxes(autorange=True)
        .update_yaxes(
            col=1,
            title="CO<sub>2</sub> emissions (GtCO<sub>2</sub>/yr)",
            title_standoff=0,
        )
    )

    fig_baseline_emissions.for_each_annotation(
        lambda a: a.update(text=a.text.split("=")[-1])
    )

    return fig_baseline_emissions
