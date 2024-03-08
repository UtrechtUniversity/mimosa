import os
import sys
import json
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
)

from mimosa import MIMOSA
from mimosa.common.config.parseconfig import check_params
from mimosa.components.welfare.utility_fct import calc_utility

params, parser_tree = check_params({}, return_parser_tree=True)

# Create an instance of the MIMOSA model to get the names of each parameter to be parsed
model = MIMOSA(params)

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


## Utility function

fig_utility = make_subplots()
x = np.linspace(0.1, 10, 100)
for elasmu, color in zip([0.5, 1.001, 1.5], COLORS):
    y = calc_utility(x, 1, elasmu)
    fig_utility.add_scatter(
        x=x,
        y=y,
        mode="lines",
        name=f"elasmu={elasmu}",
        line={
            "color": color,
            "width": 2.5,
        },
    )
fig_utility.add_scatter(
    x=x,
    y=np.log(x),
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
fig_utility.write_json("docs/assets/plots/utility_fct.json")

## Regional initial capital stock factor

fig_init_capital_factor = make_subplots()
init_capital_factor = model.regional_param_store.get("economics", "init_capital_factor")
fig_init_capital_factor.add_bar(
    x=list(init_capital_factor.keys()),
    y=list(init_capital_factor.values()),
)
fig_init_capital_factor.update_yaxes(
    title="Initial capital stock factor<br>(factor of GDP)"
).update_layout(height=300)
fig_init_capital_factor.write_json("docs/assets/plots/init_capital_factor.json")


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
).update_layout(showlegend=False, height=350, margin={"l": 0, "r": 0, "t": 0, "b": 0})

fig_regions.write_json("docs/assets/plots/image_regions.json")
