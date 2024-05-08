from mimosa import MIMOSA, load_params

params = load_params()

params["economics"]["damages"]["quantile"] = 0.95
params["temperature"]["TCRE"] = "0.82 delta_degC/(TtCO2)"
params["economics"]["PRTP"] = 0.001

model2 = MIMOSA(params)
model2.solve()

model2.save("run_example2")
