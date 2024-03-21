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

## Create regional parameter plots

for param_category, param_name, y_title in [
    (
        "economics",
        "init_capital_factor",
        "Initial capital stock factor<br>(factor of GDP)",
    ),
    (
        "MAC",
        "kappa_rel_abatement_0.75_2050",
        "Regional MAC scaling factor<br>(factor of global MAC)",
    ),
]:
    fig_init_capital_factor = make_subplots()
    init_capital_factor = model.regional_param_store.get(param_category, param_name)
    fig_init_capital_factor.add_bar(
        x=list(init_capital_factor.keys()),
        y=list(init_capital_factor.values()),
    )
    fig_init_capital_factor.update_yaxes(title=y_title).update_layout(height=300)
    fig_init_capital_factor.write_json(
        f"docs/assets/plots/{param_category}_{param_name}.json"
    )


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


## Baseline emissions
data = pd.read_csv("mimosa/inputdata/data/data_IMAGE_SSP_harmonised_2020.csv")
data_emissions = (
    data.drop(columns=["Model", "Unit"])
    .set_index(["Scenario", "Region", "Variable"])
    .rename_axis("Year", axis=1)
    .stack()
)
data_emissions = data_emissions.unstack("Variable").reset_index().astype({"Year": int})
data_emissions["Emissions|CO2"] /= 1000
data_emissions["Scenario"] = data_emissions["Scenario"].str.split("-").str[0]

fig_baseline_emissions = px.line(
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

fig_baseline_emissions.update_layout(
    legend={"orientation": "h", "y": -1.05, "x": 0.5, "xanchor": "center"},
    margin={"r": 30, "t": 30, "l": 50},
)
(
    fig_baseline_emissions.update_xaxes(title=None, range=[2021, 2100])
    .update_yaxes(autorange=True)
    .update_yaxes(
        col=1, title="CO<sub>2</sub> emissions (GtCO<sub>2</sub>/yr)", title_standoff=0
    )
)

fig_baseline_emissions.for_each_annotation(
    lambda a: a.update(text=a.text.split("=")[-1])
)
fig_baseline_emissions.write_json("docs/assets/plots/baseline_emissions.json")


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
        x=x,
        y=TCRE * x / 1000,
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

fig_ar5_tcre.write_json("docs/assets/plots/ar5_tcre.json")


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
        x=x,
        y=(x - 2200) * TCRE / 1000 + 1 + yshift,
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
fig_ar6_tcre.write_json("docs/assets/plots/ar6_tcre.json")
