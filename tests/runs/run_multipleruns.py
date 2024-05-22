from mimosa import MIMOSA, load_params

for budget in ["500 GtCO2", "700 GtCO2", "1000 GtCO2"]:

    params = load_params()

    params["emissions"]["carbonbudget"] = budget

    model3 = MIMOSA(params)
    model3.solve()

    model3.save(f"run_example3_{budget}")  # (1)!
