import os
import sys
import numpy as np
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

## Regional initial capital stock factor

fig_init_capital_factor = make_subplots()
init_capital_factor = model.regional_param_store.get("economics", "init_capital_factor")
fig_init_capital_factor.add_bar(
    x=list(init_capital_factor.keys()),
    y=list(init_capital_factor.values()),
)
fig_init_capital_factor.update_yaxes(
    title="Initial capital stock factor<br>(factor of GDP)"
).update_layout(height=300)
fig_init_capital_factor.write_json("docs/assets/plots/init_capital_factor.json")
