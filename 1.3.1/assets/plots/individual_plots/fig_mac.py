import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from .common import mimosa, model, COLORS, params


def create_fig():

    ##############
    # Make MAC figure
    ##############

    fig_mac = make_subplots()

    x = np.arange(0, 1.02, 0.01)

    def mitigcosts(x):
        return 2601 * x**3

    fig_mac.add_scatter(x=x, y=mitigcosts(x), name="MAC", showlegend=False)

    reduct = 0.8
    x2 = np.arange(0, reduct + 0.01, 0.01)
    fig_mac.add_scatter(
        x=list(x2),
        y=list(mitigcosts(x2)),
        fill="tozeroy",
        showlegend=False,
        line_color="rgba(0,0,0,0)",
        fillcolor="rgba(151, 206, 228, .5)",
    )
    fig_mac.add_scatter(
        x=[reduct],
        y=[mitigcosts(reduct)],
        marker={"size": 12, "color": "rgb(151, 206, 228)"},
        showlegend=False,
        name="MAC for 80%",
    )
    fig_mac.add_annotation(
        x=0.65,
        y=400,
        ax=-50,
        ay=-100,
        text="Mitigation costs<br>(area under MAC)<br>for reduction of 80%",
        arrowhead=6,
        arrowwidth=1.5,
        arrowcolor="#666",
    )

    fig_mac.update_layout(width=600, height=400).update_xaxes(
        tickformat="p",
        title="Relative mitigation (% of baseline emissions)",
    ).update_yaxes(
        ticksuffix=" $ ",
        title="Carbon price ($/tCO<sub>2</sub>)",
        title_standoff=0,
        dtick=1000,
    )

    return fig_mac
