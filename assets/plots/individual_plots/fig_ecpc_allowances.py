##############
# ECPC effort sharing: repayment and allowances
##############

import pandas as pd
import plotly.express as px

from .common import mimosa, COLORS, MIMOSA, value, plotly_express_to_subplot


def create_fig():
    params = mimosa.load_params()
    params["time"]["end"] = 2100
    params["effort sharing"]["regime"] = "equal_cumulative_per_cap"
    params["model"]["emissiontrade module"] = "emissiontrade"
    m = MIMOSA(params, prerun=False).concrete_model
    t = list(m.t)

    global_emissions = pd.Series(
        {
            2020: 42.8173,
            2025: 32.1724,
            2030: 25.734,
            2035: 19.9271,
            2040: 17.6311,
            2045: 15.8273,
            2050: 13.6079,
            2055: 11.4742,
            2060: 9.36797,
            2065: 6.99849,
            2070: 4.21356,
            2075: 0.835655,
            2080: -2.84173,
            2085: -6.63959,
            2090: -10.7388,
            2095: -15.5117,
            2100: -6.93319,
        }
    )
    regions = ["USA", "INDIA"]

    # Future shares are based on equal per capita allowances (IEPC)
    iepc_allowances = (
        pd.DataFrame(
            {
                r: {int(m.year(t)): m.percapconv_share_pop[t, r] for t in m.t}
                for r in regions
            }
        )
        .mul(global_emissions, axis=0)
        .rename_axis("Year")
        .rename_axis("Region", axis=1)
        .T.stack()
    )

    # Historical debt repayment
    debt_repayment = (
        pd.DataFrame(
            {
                r: {
                    int(m.year(t)): value(
                        m.effortsharing_ecpc_annual_debt_repayment[t, r]
                    )
                    for t in m.t
                }
                for r in regions
            }
        )
        .rename_axis("Year")
        .rename_axis("Region", axis=1)
        .T.stack()
    )

    data = pd.DataFrame(
        {
            "Allowances": iepc_allowances - debt_repayment,
            "Debt<br>compensation/<br>repayment": -debt_repayment,
            "Per cap fair share": iepc_allowances,
        }
    ).reset_index()
    data = data[data["Year"] >= 2025]
    fig = px.line(
        data,
        x="Year",
        y=data.columns[2:],
        color="variable",
        color_discrete_sequence=[COLORS[2], COLORS[0], COLORS[1]],
        line_dash="variable",
        facet_col="Region",
        line_dash_sequence=["solid", "dot", "dot"],
        height=350,
        width=700,
    )
    fig = plotly_express_to_subplot(fig)

    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1].strip()))
    fig.update_layout(
        legend_title=None, legend_y=0.5, margin={"l": 20, "r": 20, "t": 20, "b": 20}
    )
    fig.update_xaxes(title=None)
    fig.update_yaxes(title="Yearly allowances (GtCO<sub>2</sub>/yr)", col=1)

    for text, x, y, ax, ay, col in [
        (
            " <br> Repayment for hist.<br> debt: 122.5 GtCO<sub>2</sub>",
            2032,
            -2,
            32,
            24,
            1,
        ),
        (
            " <br> Compensation for<br> hist. debt: 96.1 GtCO<sub>2</sub>",
            2032,
            2,
            0,
            45,
            2,
        ),
    ]:
        fig.add_annotation(
            text=text,
            x=x,
            y=y,
            xanchor="left",
            align="left",
            ax=ax,
            ay=ay,
            arrowhead=7,
            arrowwidth=1.5,
            arrowcolor="#AAA",
            font_color="#AAA",
            xref=f"x{col}",
            yref=f"y{col}",
        )

    def update_trace(t):
        if "Debt" in t.name:
            t.update(fill="tozeroy")

    fig.for_each_trace(update_trace)

    return fig
