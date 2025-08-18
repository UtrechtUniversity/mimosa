from mimosa import MIMOSA, load_params

params = load_params()
model = MIMOSA(params)
simulation = model.run_simulation()  # (1)!
model.save_simulation(simulation, "run_sim_default")
