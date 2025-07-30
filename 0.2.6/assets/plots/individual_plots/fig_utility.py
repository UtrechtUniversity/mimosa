import numpy as np
import pandas as pd
from plotly.subplots import make_subplots

from .common import mimosa, model, COLORS


## Utility function


def create_fig():
    fig_utility = make_subplots()
    x = np.linspace(0.1, 10, 100)
    for elasmu, color in zip([0.5, 1.001, 1.5], COLORS):
        y = mimosa.components.welfare.utility_fct.calc_utility(x, 1, elasmu)
        fig_utility.add_scatter(
            x=list(x),
            y=list(y),
            mode="lines",
            name=f"elasmu={elasmu}",
            line={
                "color": color,
                "width": 2.5,
            },
        )
    fig_utility.add_scatter(
        x=list(x),
        y=list(np.log(x)),
        mode="lines",
        name="log(x)",
        line={"color": "grey", "width": 2.5, "dash": "dot"},
    )
    fig_utility.update_layout(
        # title="Utility function for different values of elasmu",
        margin={"l": 30, "r": 30, "t": 10, "b": 30},
        height=300,
    )
    fig_utility.update_xaxes(title="Per capita consumption")
    fig_utility.update_yaxes(title="Utility")
    return fig_utility
