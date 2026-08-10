import json
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from .common import mimosa, model, COLORS, params


def create_fig():
    ### AR6 TCRE plot

    fig_ar6_tcre = make_subplots()

    ar6_sizex = 6885.2
    ar6_sizey = 5.8888
    ar6_x = -521.8
    ar6_y = -1.993

    fig_ar6_tcre.add_layout_image(
        dict(
            source="../../assets/plots/ar6_wg1_spm10.png",
            xref="x",
            yref="y",
            yanchor="bottom",
            x=ar6_x,
            y=ar6_y,
            sizex=ar6_sizex,
            sizey=ar6_sizey,
            sizing="stretch",
            opacity=1,
            layer="below",
        )
    )
    ar6_annotations = []
    for TCRE, name, yshift, xshift in (
        [0.75, "p95", 0.2, -20],
        [0.62, "p50", 0, 20],
        [0.42, "p05", -0.07, 40],
    ):
        x = np.linspace(2200, 4380)
        fig_ar6_tcre.add_scatter(
            x=list(x),
            y=list((x - 2200) * TCRE / 1000 + 1 + yshift),
            mode="lines",
            line={"color": "black", "dash": "dot", "width": 3},
            name=f"AR6 {name} (TCRE={TCRE} degC/TtCO2)",
        )
        ar6_annotations.append(
            dict(
                x=4500,
                y=(4400 - 2200) * TCRE / 1000 + 1 + yshift,
                text=f"<b> TCRE={TCRE} </b><br>({name})",
                xanchor="left",
                font={"size": 12, "color": "black"},
                showarrow=False,
                bgcolor="white",
                bordercolor="black",
            )
        )
    fig_ar6_tcre.update_layout(annotations=ar6_annotations)
    fig_ar6_tcre.update_xaxes(
        range=[ar6_x, 6000], showgrid=False, zeroline=False, visible=False
    ).update_yaxes(
        range=[-0.2, ar6_sizey + ar6_y], visible=False, showgrid=False, zeroline=False
    ).update_layout(
        width=700,
        height=440,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(
                        label="With TCRE",
                        method="update",
                        args=[
                            {"visible": [True, True, True]},
                            {"annotations": ar6_annotations},
                        ],
                    ),
                    dict(
                        label="Original figure",
                        method="update",
                        args=[{"visible": [False, False, False]}, {"annotations": []}],
                    ),
                ],
                direction="right",
                showactive=True,
                x=0.5,
                y=1.1,
                xanchor="center",
                yanchor="top",
            )
        ],
    )

    return fig_ar6_tcre
