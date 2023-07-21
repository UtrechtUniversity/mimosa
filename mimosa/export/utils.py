"""
Plot functions. Not necessary if dashboard is used.
"""
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
from pyomo.environ import value

COLORS_PBL = [
    "#00AEEF",
    "#808D1D",
    "#B6036C",
    "#FAAD1E",
    "#3F1464",
    "#7CCFF2",
    "#F198C1",
    "#42B649",
    "#EE2A23",
    "#004019",
    "#F47321",
    "#511607",
    "#BA8912",
    "#78CBBF",
    "#FFF229",
    "#0071BB",
]


class Plot:
    """
    Wrapper for a Plotly figure.

    First it creates a subplot figure, then using the function `add`,
    a trace can be added given a Pyomo variable.
    """

    def __init__(self, m, numrows=4, globalrows=None, coltitles=None, **kwargs):
        if globalrows is None:
            globalrows = [4]
        self.m = m
        self.regions = m.regions
        self.years = m.year(np.array(m.t))
        self.t = m.t

        n = len(m.regions)
        specs = [[{"secondary_y": True}] * n for _ in range(numrows)]
        for row in globalrows:
            specs[row - 1] = [{"colspan": n, "secondary_y": True}] + [None] * (n - 1)

        self.fig = make_subplots(
            numrows,
            n,
            shared_yaxes=True,
            shared_xaxes="rows",
            specs=specs,
            subplot_titles=coltitles if coltitles is not None else list(m.regions),
            **kwargs
        )

        # Make sure all secondary yaxes are matched per row
        for i in range(numrows):
            ref = next(self.fig.select_yaxes(row=i + 1, col=1, secondary_y=True))
            ref_name = ref.plotly_name.replace("axis", "")
            for axis in self.fig.select_yaxes(row=i + 1, secondary_y=True):
                axis.matches = ref_name

        self.curr_values = {}

    def _value(self, var, region, is_fct):
        if is_fct:
            return [var(t, region) for t in self.years]
        else:
            return [value(var[t, region]) for t in self.t]

    def _value_global(self, var, is_fct):
        if is_fct:
            return [var(t) for t in self.t]
        else:
            return [value(var[t]) for t in self.t]

    def add_scatter(self, values, name, color, row, col, showlegend, **kwargs):
        self.fig.add_scatter(
            x=self.years,
            y=values,
            name=name,
            legendgroup=name,
            line_color=color,
            row=row,
            col=col,
            showlegend=showlegend,
            **(
                {"line_dash": "dot" if kwargs.get("secondary_y", False) else "solid"}
                if "line_dash" not in kwargs
                else {}
            ),
            **kwargs
        )

    def add(self, var, is_regional=True, is_fct=False, name=None, row=1, **kwargs):

        if not is_fct and name is None:
            name = var.name
        new = name not in self.curr_values

        if new:
            self.curr_values[name] = len(self.curr_values)
        color = COLORS_PBL[self.curr_values[name] % len(COLORS_PBL)]

        if is_regional:
            for i, r in enumerate(self.regions):
                self.add_scatter(
                    self._value(var, r, is_fct),
                    name,
                    color,
                    row,
                    col=i + 1,
                    showlegend=new and (i == 0),
                    **kwargs
                )
        else:
            self.add_scatter(
                self._value_global(var, is_fct),
                name,
                color,
                row,
                col=1,
                showlegend=new,
                **kwargs
            )

    def set_layout(self):
        self.fig.update_xaxes(range=[self.years[0], 2100])
        for i in range(1, len(self.regions)):
            self.fig.update_yaxes(secondary_y=True, showticklabels=False, col=i)
        self.fig.update_traces(mode="lines")
        self.fig.update_layout(
            margin={"t": 50, "l": 50, "r": 50, "b": 50},
            legend={"yanchor": "middle", "y": 0.5},
        )

    def set_yaxes_titles(self, titles):
        for i, title in enumerate(titles):
            self.fig.update_yaxes(title=title, row=i + 1, col=1, secondary_y=False)

    def show(self):
        self.set_layout()
        return self.fig


def visualise_ipopt_output(output_file):
    file = open(output_file, "r")
    in_iterations = False

    iterations = []

    for line in file:
        if line.startswith("iter "):
            in_iterations = True
        if line.strip() == "":
            in_iterations = False

        if in_iterations and line.startswith(" "):
            split = line.strip().split(" ")[:4]

            # Check if it was a recovered iteration
            if "r" in split[0]:
                recovered = True
                split = split[0].split("r") + split[1:-1]
            else:
                recovered = False
            iterations.append(split + [recovered])

    iterations_df = pd.DataFrame(
        iterations, columns=["iter", "objective", "inf_pr", "inf_du", "recovered"]
    )
    iterations_df = iterations_df.astype(
        {"iter": int, "objective": float, "inf_pr": float, "inf_du": float}
    )

    file.close()

    fig = (
        px.scatter(
            iterations_df,
            x="iter",
            y=["objective", "inf_pr", "inf_du"],
            facet_row="variable",
            color="recovered",
        )
        .update_yaxes(matches=None, type="log")
        .update_yaxes(row=3, type="linear")
    )

    fig.write_html(output_file.split(".")[0] + ".html", include_plotlyjs="cdn")
