from mimosa import MIMOSA, load_params

model = MIMOSA(load_params())

simulation = model.run_simulation(relative_abatement=0.25)
model.save_simulation(simulation, "constant_25_percent_abatement")
