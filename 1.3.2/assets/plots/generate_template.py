import os
import json

dir_path = os.path.dirname(os.path.realpath(__file__))

template = {
    "barmode": "relative",
    "coloraxis": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
    "colorway": [
        "#97CEE4",
        "#778663",
        "#6F7899",
        "#A7C682",
        "#8CA7D0",
        "#FAC182",
        "#F18872",
        "#bd7161",
    ],
    "font": {
        "color": "#25292b",
        "family": '"Frutiger LT Pro Condensed", "FrutigerLTPro-Condensed", "Open Sans", verdana, arial, sans-serif',
        "size": 15.203926164664518,
    },
    "legend": {
        "font": {"size": 15.203926164664518},
        "title": {"font": {"size": 15.203926164664518}},
        "tracegroupgap": 0,
    },
    "margin": {"r": 50, "t": 20},
    "plot_bgcolor": "#F5F5F5",
    "title": {
        "font": {
            "family": '"Frutiger LT Pro Condensed", "FrutigerLTPro-Condensed", "Open Sans", verdana, arial, sans-serif',
            "size": 23.89188397304424,
        },
        "x": 0.01,
        "xanchor": "left",
    },
    "xaxis": {
        "automargin": True,
        "linecolor": "rgba(0,0,0,0)",
        "showgrid": False,
        "ticks": "",
        "title": {"font": {"size": 17.37591561675945}, "standoff": 0},
        "zerolinecolor": "#8e8e8d",
        "zerolinewidth": 2,
    },
    "yaxis": {
        "automargin": True,
        "gridcolor": "#d0d0d0",
        "linecolor": "rgba(0,0,0,0)",
        "gridwidth": 0.5429973630237328,
        "ticks": "",
        "title": {"font": {"size": 17.37591561675945}, "standoff": 0},
        "zerolinecolor": "#8e8e8d",
        "zerolinewidth": 2,
    },
}

template_slate = {
    "autotypenumbers": "strict",
    "colorway": [
        "#97CEE4",
        "#778663",
        "#6F7899",
        "#A7C682",
        "#8CA7D0",
        "#FAC182",
        "#F18872",
        "#bd7161",
    ],
    "font": {"color": "#f2f5fa"},
    "hovermode": "closest",
    "hoverlabel": {"align": "left"},
    "paper_bgcolor": "rgba(17,17,17,0)",
    "plot_bgcolor": "rgb(17,17,17)",
    "polar": {
        "bgcolor": "rgb(17,17,17)",
        "angularaxis": {"gridcolor": "#506784", "linecolor": "#506784", "ticks": ""},
        "radialaxis": {"gridcolor": "#506784", "linecolor": "#506784", "ticks": ""},
    },
    "ternary": {
        "bgcolor": "rgb(17,17,17)",
        "aaxis": {"gridcolor": "#506784", "linecolor": "#506784", "ticks": ""},
        "baxis": {"gridcolor": "#506784", "linecolor": "#506784", "ticks": ""},
        "caxis": {"gridcolor": "#506784", "linecolor": "#506784", "ticks": ""},
    },
    "coloraxis": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
    "colorscale": {
        "sequential": [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
        ],
        "sequentialminus": [
            [0.0, "#0d0887"],
            [0.1111111111111111, "#46039f"],
            [0.2222222222222222, "#7201a8"],
            [0.3333333333333333, "#9c179e"],
            [0.4444444444444444, "#bd3786"],
            [0.5555555555555556, "#d8576b"],
            [0.6666666666666666, "#ed7953"],
            [0.7777777777777778, "#fb9f3a"],
            [0.8888888888888888, "#fdca26"],
            [1.0, "#f0f921"],
        ],
        "diverging": [
            [0, "#8e0152"],
            [0.1, "#c51b7d"],
            [0.2, "#de77ae"],
            [0.3, "#f1b6da"],
            [0.4, "#fde0ef"],
            [0.5, "#f7f7f7"],
            [0.6, "#e6f5d0"],
            [0.7, "#b8e186"],
            [0.8, "#7fbc41"],
            [0.9, "#4d9221"],
            [1, "#276419"],
        ],
    },
    "xaxis": {
        "gridcolor": "#283442",
        "zerolinecolor": "#283442",
        "automargin": True,
        "linecolor": "rgba(0,0,0,0)",
        "showgrid": False,
        "ticks": "",
        "title": {"font": {"size": 17.37591561675945}, "standoff": 0},
        "zerolinewidth": 2,
    },
    "yaxis": {
        "gridcolor": "#283442",
        "zerolinecolor": "#444466",
        "automargin": True,
        "linecolor": "rgba(0,0,0,0)",
        "gridwidth": 0.5429973630237328,
        "ticks": "",
        "title": {"font": {"size": 17.37591561675945}, "standoff": 0},
        "zerolinewidth": 2,
    },
    "scene": {
        "xaxis": {
            "backgroundcolor": "rgb(17,17,17)",
            "gridcolor": "#506784",
            "linecolor": "#506784",
            "showbackground": True,
            "ticks": "",
            "zerolinecolor": "#C8D4E3",
            "gridwidth": 2,
        },
        "yaxis": {
            "backgroundcolor": "rgb(17,17,17)",
            "gridcolor": "#506784",
            "linecolor": "#506784",
            "showbackground": True,
            "ticks": "",
            "zerolinecolor": "#C8D4E3",
            "gridwidth": 2,
        },
        "zaxis": {
            "backgroundcolor": "rgb(17,17,17)",
            "gridcolor": "#506784",
            "linecolor": "#506784",
            "showbackground": True,
            "ticks": "",
            "zerolinecolor": "#C8D4E3",
            "gridwidth": 2,
        },
    },
    "shapedefaults": {"line": {"color": "#f2f5fa"}},
    "annotationdefaults": {"arrowcolor": "#f2f5fa", "arrowhead": 0, "arrowwidth": 1},
    "geo": {
        "bgcolor": "rgb(17,17,17)",
        "landcolor": "rgb(17,17,17)",
        "subunitcolor": "#506784",
        "showland": True,
        "showlakes": True,
        "lakecolor": "rgb(17,17,17)",
    },
    "title": {"x": 0.05},
    "updatemenudefaults": {"bgcolor": "#506784", "borderwidth": 0},
    "sliderdefaults": {
        "bgcolor": "#C8D4E3",
        "borderwidth": 1,
        "bordercolor": "rgb(17,17,17)",
        "tickwidth": 0,
    },
    "mapbox": {"style": "dark"},
}

for subplot_i in range(2, 30):
    template[f"xaxis{subplot_i}"] = template["xaxis"]
    template[f"yaxis{subplot_i}"] = template["yaxis"]
    template_slate[f"xaxis{subplot_i}"] = template_slate["xaxis"]
    template_slate[f"yaxis{subplot_i}"] = template_slate["yaxis"]

with open(f"{dir_path}/template.json", "w") as f:
    json.dump(template, f)

with open(f"{dir_path}/template_slate.json", "w") as f:
    json.dump(template_slate, f)
