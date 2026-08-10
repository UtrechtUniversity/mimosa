from mimosa import MIMOSA, load_params

# First run MIMOSA in optimisation mode

params = load_params()

for slr_estimate in ["low", "central", "high"]:
    params["model structure"]["sealevelrise options"]["projection"] = slr_estimate
    model1 = MIMOSA(params)
    simulation = model1.run_nopolicy_baseline()

    model1.save_simulation(simulation, f"baseline_nopolicy_slr_{slr_estimate}")
