import json
import numpy as np
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots

from individual_plots import (
    fig_ecpc_historical_debt,
    fig_ecpc_allowances,
    fig_utility,
    fig_init_capital_and_kappa,
    fig_region_map,
    fig_baseline_emissions,
    fig_ar5_tcre,
    fig_ar6_tcre,
    fig_mac,
    table_coacch_slr,
)

figure_ecpc_debt = fig_ecpc_historical_debt.create_fig()
figure_ecpc_debt.write_json("docs/assets/plots/ecpc_debt.json")

figure_ecpc_allowances = fig_ecpc_allowances.create_fig()
figure_ecpc_allowances.write_json("docs/assets/plots/ecpc_allowances.json")

figure_utility = fig_utility.create_fig()
figure_utility.write_json("docs/assets/plots/utility_fct.json")

figs_init_capital_and_kappa = fig_init_capital_and_kappa.create_fig()
for name, fig in figs_init_capital_and_kappa.items():
    fig.write_json(f"docs/assets/plots/{name}.json")


figure_region_map = fig_region_map.create_fig()
figure_region_map.write_json("docs/assets/plots/image_regions.json")

figure_baseline_emissions = fig_baseline_emissions.create_fig()
figure_baseline_emissions.write_json("docs/assets/plots/baseline_emissions.json")

figure_ar5_tcre = fig_ar5_tcre.create_fig()
figure_ar5_tcre.write_json("docs/assets/plots/ar5_tcre.json")

figure_ar6_tcre = fig_ar6_tcre.create_fig()
figure_ar6_tcre.write_json("docs/assets/plots/ar6_tcre.json")

figure_mac = fig_mac.create_fig()
figure_mac.write_json("docs/assets/plots/mac_explanation.json")

table_slr = table_coacch_slr.create_table()
table_slr.to_csv("docs/assets/data/coacch_slr_form.csv")
