import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pyomo.environ import value

COLORS_PBL = ['#00AEEF', '#808D1D', '#B6036C', '#FAAD1E', '#3F1464', '#7CCFF2', '#F198C1', '#42B649', '#EE2A23', '#004019', '#F47321', '#511607', '#BA8912', '#78CBBF', '#FFF229', '#0071BB']


class Plot:
    
    def __init__(self, m, numrows=4, globalrows=[4], coltitles=None, **kwargs):
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
            shared_yaxes=True, shared_xaxes='rows', specs=specs,
            subplot_titles=coltitles if coltitles is not None else list(m.regions),
            **kwargs
        )

        # Make sure all secondary yaxes are matched per row
        for i in range(numrows):
            ref = next(self.fig.select_yaxes(row=i+1, col=1, secondary_y=True))
            ref_name = ref.plotly_name.replace('axis', '')
            for ax in self.fig.select_yaxes(row=i+1, secondary_y=True):
                ax.matches = ref_name

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
            **({'line_dash': 'dot' if kwargs.get('secondary_y', False) else 'solid'} if 'line_dash' not in kwargs else {}),
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




