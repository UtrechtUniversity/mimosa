import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from model.common.config import params
from model.common import data

COLORS_PBL = ['#00AEEF', '#808D1D', '#B6036C', '#FAAD1E', '#3F1464', '#7CCFF2', '#F198C1', '#42B649', '#EE2A23', '#004019', '#F47321', '#511607', '#BA8912', '#78CBBF', '#FFF229', '#0071BB']

def full_plot(m, regions, years):
    fig = make_subplots(
        3, len(regions),
        subplot_titles=list(regions.keys()),
        shared_yaxes=True,
        vertical_spacing=0.05,
        horizontal_spacing=0.02,
        specs=[[{'secondary_y': True}] * len(regions), [{}] * len(regions), [{'colspan': len(regions), 'secondary_y': True}]+[None]*(len(regions)-1)]
    )

    for i, region in enumerate(regions):
        fig.add_scatter(x=years, y=m.baseline_emissions[i].value, name='Baseline emissions', line_color=COLORS_PBL[0], row=1, col=i+1, legendgroup='0', showlegend=i==0)
        fig.add_scatter(x=years, y=m.regional_emissions[i].value, name='Emissions', line_color=COLORS_PBL[1], row=1, col=i+1, legendgroup='1', showlegend=i==0)
        fig.add_scatter(x=years, y=m.carbonprice[i].value, name='Carbon price', line_color=COLORS_PBL[5], line_dash='dot', secondary_y=True, row=1, col=i+1, legendgroup='1b', showlegend=i==0, visible="legendonly")
        # fig.add_scatter(x=years, y=m.relative_abatement[i].value, name='Relative abatement', line_color=COLORS_PBL[1], line_dash='dot', secondary_y=True, row=1, col=i+1, legendgroup='1b', showlegend=i==0, visible="legendonly")

        fig.add_scatter(x=years, y=m.capital_stock[i].value, name='Capital stock', line_color=COLORS_PBL[4], row=2, col=i+1, legendgroup='4', showlegend=i==0)
        fig.add_scatter(x=years, y=m.GDP_net[i].value, name='GDP net', line_color=COLORS_PBL[2], row=2, col=i+1, legendgroup='2', showlegend=i==0)
        fig.add_scatter(x=years, y=m.abatement_costs[i].value, name='Abatement costs', line_color=COLORS_PBL[3], row=2, col=i+1, legendgroup='3', showlegend=i==0)
        # fig.add_scatter(x=years, y=L[i].value, name='population', line_color=COLORS_PBL[5], row=2, col=i+1, legendgroup='5', showlegend=i==0, visible="legendonly")
        # fig.add_scatter(x=years, y=utility[i].value, name='utility', line_color=COLORS_PBL[9], row=2, col=i+1, legendgroup='6', showlegend=i==0, visible="legendonly")


    fig.add_scatter(x=years, y=m.global_emissions.value, name='Global emissions', line_color=COLORS_PBL[10], row=3, col=1)
    fig.add_scatter(x=years, y=m.cumulative_emissions.value, name='Cumulative emissions', line_color=COLORS_PBL[7], row=3, col=1, visible="legendonly")
    # fig.add_scatter(x=years, y=temperature.value, name='Temperature', line_color=COLORS_PBL[8], row=3, col=1, secondary_y=True)

    fig.update_xaxes(range=[params['time']['start'],2100])
    fig.update_yaxes(title='GtCO<sub>2</sub>/yr', row=1, col=1, secondary_y=False)
    fig.update_yaxes(title='trillion US$2005/yr', row=2, col=1)
    fig.update_yaxes(title='GtCO<sub>2</sub>/yr', row=3, col=1)
    fig.update_layout(margin={'t': 50, 'l': 50, 'r': 50, 'b': 50}, legend={'yanchor': 'middle', 'y': 0.5})

    fig.write_html('temp.html')
