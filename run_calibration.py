import os
import numpy as np
import pandas as pd
from mimosa import MIMOSA, load_params

params = load_params()

params["economics"]["damages"]["ignore damages"] = True
params["time"]["end"] = 2100

try:
    os.mkdir("output/calibration")
except FileExistsError:
    pass

carbon_budgets = np.arange(200, 1501, 100)

for budget in carbon_budgets:
    params["emissions"]["carbonbudget"] = f"{budget} GtCO2"

    model = MIMOSA(params)
    model.solve()
    model.save(f"calibration/cb_{budget}")

# Calculate the NPV of the mitigation costs for each run:


def npv(values, discount_rate):
    years = values.index.astype(float)
    t = years - years[0]
    discount_factor = np.exp(-discount_rate * t)
    return np.trapezoid(values * discount_factor, t)


for budget in carbon_budgets:
    outp = pd.read_csv(f"output/calibration/cb_{budget}.csv")
    global_mitig_costs = outp.loc[outp["Variable"] == "mitigation_costs", "2020":].sum(
        axis=0
    )
    global_gdp_gross = outp.loc[outp["Variable"] == "GDP_gross", "2020":].sum(axis=0)
    r = 0.03
    npv_costs = npv(global_mitig_costs, r) / npv(global_gdp_gross, r)
    print(f"NPV of mitigation costs for {budget} GtCO2: {npv_costs:.1%}")
