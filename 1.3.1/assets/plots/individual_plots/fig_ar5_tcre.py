import json
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from .common import mimosa, model, COLORS, params


def create_fig():
    ### AR5 TCRE plot

    from plotly.subplots import make_subplots

    fig_ar5_tcre = make_subplots()

    fig_ar5_tcre.add_layout_image(
        dict(
            source="../../assets/plots/ar5_wg1_spm10.jpeg",
            xref="x",
            yref="y",
            yanchor="bottom",
            x=-790,
            y=-1.01,
            sizex=10232,
            sizey=6.677,
            sizing="stretch",
            opacity=1,
            layer="below",
        )
    )

    ar5_annotations = []
    for TCRE, name, xend, xshift in (
        [0.82, "p95", 6000, -20],
        [0.62, "p50", 8000, 20],
        [0.42, "p05", 9100, 40],
    ):
        x = np.linspace(1000, xend)
        fig_ar5_tcre.add_scatter(
            x=list(x),
            y=list(TCRE * x / 1000),
            mode="lines",
            line={"color": "black", "dash": "dot", "width": 3},
            name=f"AR5 {name} (TCRE={TCRE} degC/TtCO2)",
        )
        ar5_annotations.append(
            dict(
                x=5000,
                y=TCRE * 5000 / 1000,
                text=f"<b> TCRE={TCRE} </b><br>({name})",
                xanchor="right" if name == "p95" else "left",
                font={"size": 12, "color": "black"},
                showarrow=False,
                xshift=xshift,
                bgcolor="white",
                bordercolor="black",
            )
        )
    fig_ar5_tcre.update_layout(annotations=ar5_annotations)
    fig_ar5_tcre.update_xaxes(
        range=[-790, 10232 - 790], showgrid=False, zeroline=False, visible=False
    ).update_yaxes(
        range=[-1.01, 6.677 - 1.01], visible=False, showgrid=False, zeroline=False
    ).update_layout(
        width=700,
        height=550,
        margin={"r": 100, "t": 0, "l": 0, "b": 0},
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
                            {"annotations": ar5_annotations},
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

    return fig_ar5_tcre
