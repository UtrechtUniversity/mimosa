import os
import sys

from plotly.subplots import make_subplots

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
)


import mimosa
from mimosa import MIMOSA
from mimosa.common.config.parseconfig import check_params
from mimosa.common import value


params, parser_tree = check_params({}, return_parser_tree=True)


# Create an instance of the MIMOSA model to get the names of each parameter to be parsed
model = MIMOSA(params, prerun=False)
param_store = model.preprocessor._regional_param_store

COLORS = [
    "#5492cd",
    "#ffa900",
    "#003466",
    "#EF550F",
    "#990002",
    "#c47900",
    "#00aad0",
    "#76797b",
]


def plotly_express_to_subplot(fig_express):
    fig = make_subplots()
    for trace in fig_express.data:
        fig.add_scatter(
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

    fig.layout = fig_express.layout
    return fig
