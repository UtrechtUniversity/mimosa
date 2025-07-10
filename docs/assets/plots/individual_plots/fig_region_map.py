import json
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.express as px
from .common import mimosa, model, COLORS, params


def create_fig():
    ## Regional definitions and map:

    with open("mimosa/inputdata/regions/IMAGE26_regions.json") as fh:
        regions = json.load(fh)

    image_regions = list(params["regions"].keys())
    region_df = (
        pd.Series(dict(zip(image_regions, image_regions)), name="i")
        .to_frame()
        .reset_index()
        .rename(columns={"index": "region"})
    )
    fig_regions = px.choropleth(
        region_df,
        geojson=regions,
        color="region",
        locations="region",
        labels="region",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_regions.update_geos(
        projection_type="natural earth",
        visible=False,
        showframe=True,
        framecolor="#AAA",
        showland=True,
        landcolor="#F5F5F5",
    ).update_layout(
        showlegend=False, height=350, margin={"l": 0, "r": 0, "t": 0, "b": 0}
    )

    return fig_regions
