##############
# ECPC effort sharing debt
##############

import pandas as pd
from plotly.subplots import make_subplots

from .common import mimosa, model, COLORS


class MockEcpcModel:
    def __init__(self, start_year, begin_year, discount_rate):
        self.effortsharing_ecpc_start_year = start_year
        self.beginyear = begin_year
        self.effortsharing_ecpc_discount_rate = discount_rate


def create_fig():
    ecpc_hist_emissions, ecpc_hist_population = (
        mimosa.components.effortsharing.equal_cumulative_per_cap._load_data()
    )

    ecpc_debts = {}

    for year in [1850, 1990]:
        for discount_rate in 0.01, 0.03, 0.05:
            mock_m = MockEcpcModel(year, 2020, discount_rate)
            ecpc_debts[f"    r=<b>{discount_rate}</b><br><b>{year}</b>-2020"] = (
                pd.Series(
                    {
                        r: mimosa.components.effortsharing.equal_cumulative_per_cap._calc_debt(
                            mock_m, r, ecpc_hist_emissions, ecpc_hist_population
                        )
                        for r in model.concrete_model.regions
                    },
                ).rename_axis("Region", axis=0)
            )

    ecpc_debts = pd.DataFrame(ecpc_debts).reset_index()

    fig_ecpc_debt = make_subplots()

    for i, discount_rate in enumerate(ecpc_debts.columns[1:]):
        fig_ecpc_debt.add_bar(
            x=list(ecpc_debts["Region"]),
            y=list(ecpc_debts[discount_rate]),
            name=discount_rate,
            marker_color=COLORS[i],
            visible=i == 1,
            orientation="v",
        )

    def _legend(i, n):
        visible = [False] * n
        visible[i] = True
        return visible

    fig_ecpc_debt.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                buttons=[
                    dict(
                        label=name,
                        method="update",
                        args=[
                            {"visible": _legend(i, len(ecpc_debts.columns) - 1)},
                            {"annotations": []},
                        ],
                    )
                    for i, name in enumerate(ecpc_debts.columns[1:])
                ],
                direction="right",
                showactive=True,
                active=1,
                x=0.5,
                y=1.15,
                xanchor="center",
                yanchor="top",
            ),
        ],
        margin={"l": 20, "r": 0, "t": 50, "b": 20},
        # width=800,
    ).update_yaxes(
        range=[ecpc_debts.iloc[:, 1:].min().min(), ecpc_debts.iloc[:, 1:].max().max()],
        title="Debt (in GtCO<sub>2</sub>)",
        title_standoff=0,
    )

    return fig_ecpc_debt
