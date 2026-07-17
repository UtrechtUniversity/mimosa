import numpy as np
import pandas as pd
from plotly.subplots import make_subplots

from .common import mimosa, model, COLORS, param_store


def create_fig():

    ## Create regional parameter plots

    figs = {}

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
        init_capital_factor = param_store.get(param_category, param_name)
        fig_init_capital_factor.add_bar(
            x=list(init_capital_factor.keys()),
            y=list(init_capital_factor.values()),
        )
        fig_init_capital_factor.update_yaxes(title=y_title).update_layout(height=300)

        figs[f"{param_category}_{param_name}"] = fig_init_capital_factor
    return figs
