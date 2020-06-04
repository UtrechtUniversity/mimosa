import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyomo.environ import value

COLORS_PBL = ['#00AEEF', '#808D1D', '#B6036C', '#FAAD1E', '#3F1464', '#7CCFF2', '#F198C1', '#42B649', '#EE2A23', '#004019', '#F47321', '#511607', '#BA8912', '#78CBBF', '#FFF229', '#0071BB']


class Plot:
    
    def __init__(self, m, numrows=3, globalrows=[3], coltitles=None, **kwargs):
        self.m = m
        self.regions = m.regions
        self.years = value(m.beginyear) + np.array(m.t)
        self.t = m.t
        
        n = len(m.regions)
        specs = [[{'secondary_y': True}] * n for _ in range(numrows)]
        for row in globalrows:
            specs[row-1] = [{'colspan': n, 'secondary_y': True}] + [None]*(n-1)
            
        self.fig = make_subplots(
            numrows, n,
            shared_yaxes=True, specs=specs,
            subplot_titles=coltitles if coltitles is not None else list(m.regions),
            **kwargs
        )
        self.curr_values = {}
    
    def _value(self, var, region, is_fct):
        if is_fct:
            return [var(t, region) for t in self.t]
        else:
            return [value(var[t,region]) for t in self.t]
    
    def _value_global(self, var, is_fct):
        if is_fct:
            return [var(t) for t in self.t]
        else:
            return [value(var[t]) for t in self.t]
    
    def add_scatter(self, value, name, color, row, col, showlegend, **kwargs):
        self.fig.add_scatter(
            x=self.years, y=value,
            name=name, legendgroup=name,
            line_color=color,
            row=row, col=col,
            showlegend=showlegend,
            **kwargs
        )
    
    def add(self, var, is_regional=True, is_fct=False, name=None, row=1, **kwargs):
        
        if not is_fct and name == None:
            name = var.name
        new = name not in self.curr_values

        if new:
            self.curr_values[name] = len(self.curr_values)
        color = COLORS_PBL[self.curr_values[name]]
        
        if is_regional:
            for i, r in enumerate(self.regions):
                value = self._value(var, r, is_fct)
                self.add_scatter(value, name, color, row, col=i+1, showlegend=new and (i==0), **kwargs)
        else:
            value = self._value_global(var, is_fct)
            self.add_scatter(value, name, color, row, col=1, showlegend=new, **kwargs)
        
    def set_layout(self):
        self.fig.update_xaxes(range=[self.years[0], 2100])
        self.fig.update_traces(mode='lines')
        self.fig.update_layout(
            margin={'t': 50, 'l': 50, 'r': 50, 'b': 50},
            legend={'yanchor': 'middle', 'y': 0.5}
        )
        
    def set_yaxes_titles(self, titles):
        for i, title in enumerate(titles):
            self.fig.update_yaxes(title=title, row=i+1, col=1, secondary_y=False)
        
    def show(self):
        self.set_layout()
        return self.fig









############ OLD

def full_plot(m, regions, years, params):
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
        fig.add_scatter(x=years, y=m.relative_abatement[i].value, name='Relative abatement', line_color=COLORS_PBL[1], line_dash='dot', secondary_y=True, row=1, col=i+1, legendgroup='1b', showlegend=i==0, visible="legendonly")

        fig.add_scatter(x=years, y=m.capital_stock[i].value, name='Capital stock', line_color=COLORS_PBL[4], row=2, col=i+1, legendgroup='4', showlegend=i==0)
        fig.add_scatter(x=years, y=m.GDP_gross[i].value, name='GDP gross', line_color=COLORS_PBL[2], line_dash='dot', row=2, col=i+1, legendgroup='2', showlegend=i==0)
        fig.add_scatter(x=years, y=m.GDP_net[i].value, name='GDP net', line_color=COLORS_PBL[2], row=2, col=i+1, legendgroup='2', showlegend=i==0)
        fig.add_scatter(x=years, y=m.abatement_costs[i].value, name='Abatement costs', line_color=COLORS_PBL[3], row=2, col=i+1, legendgroup='3', showlegend=i==0)
        fig.add_scatter(x=years, y=m.damage_costs[i].value, name='Damage costs', line_color=COLORS_PBL[3], row=2, col=i+1, legendgroup='3', showlegend=i==0)
        # fig.add_scatter(x=years, y=L[i].value, name='population', line_color=COLORS_PBL[5], row=2, col=i+1, legendgroup='5', showlegend=i==0, visible="legendonly")
        fig.add_scatter(x=years, y=m.utility[i].value, name='utility', line_color=COLORS_PBL[9], row=2, col=i+1, legendgroup='6', showlegend=i==0, visible="legendonly")


    fig.add_scatter(x=years, y=m.global_emissions.value, name='Global emissions', line_color=COLORS_PBL[10], row=3, col=1)
    fig.add_scatter(x=years, y=m.cumulative_emissions.value, name='Cumulative emissions', line_color=COLORS_PBL[7], row=3, col=1, visible="legendonly")
    fig.add_scatter(x=years, y=m.temperature.value, name='Temperature', line_color=COLORS_PBL[8], row=3, col=1, secondary_y=True)

    fig.update_xaxes(range=[params['time']['start'],2100])
    fig.update_yaxes(title='GtCO<sub>2</sub>/yr', row=1, col=1, secondary_y=False)
    fig.update_yaxes(title='trillion US$2005/yr', row=2, col=1)
    fig.update_yaxes(title='GtCO<sub>2</sub>/yr', row=3, col=1)
    fig.update_layout(margin={'t': 50, 'l': 50, 'r': 50, 'b': 50}, legend={'yanchor': 'middle', 'y': 0.5})

    fig.write_html('output/temp.html')
