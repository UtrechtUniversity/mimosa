from mimosa import MIMOSA, load_params

params = load_params()

params["emissions"]["carbonbudget"] = False
params["economics"]["damages"]["ignore damages"] = True

params["model"]["welfare module"] = "cost_minimising"

# Disable some emission reduction constraints
params["emissions"]["non increasing emissions after 2100"] = False
params["emissions"]["not positive after budget year"] = False
params["emissions"]["inertia"]["regional"] = False
params["emissions"]["inertia"]["global"] = False

params["time"]["end"] = 2150

model = MIMOSA(params)
model.solve()
model.save("baseline_ignore_damages")
