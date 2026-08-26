from mimosa import MIMOSA, load_params
from random import random

# First run MIMOSA in optimisation mode

params = load_params()
params["time"]["dt"] = 10
params["time"]["end"] = 2300
params["emissions"]["non increasing emissions after 2100"] = False

# From Deutloff et al. (2025)
PFAT_prob_245 = 0.857
LABC_prob_245 = 0.69
AMOC_prob_245 = 0.183
AMAZ_prob_245 = 0.141  

PFAT_rand = random()
LABC_rand = random()
AMOC_rand = random()
AMAZ_rand = random()

if (PFAT_rand < PFAT_prob_245):
    params["model structure"]["tippingpoints options"]["include PFAT"] = True

if (LABC_rand < LABC_prob_245):
    params["model structure"]["tippingpoints options"]["include LABC"] = True

if (AMOC_rand < AMOC_prob_245):
    params["model structure"]["tippingpoints options"]["include AMOC"] = True

if (AMAZ_rand < AMAZ_prob_245):
    params["model structure"]["tippingpoints options"]["include AMAZ"] = True



model1 = MIMOSA(params)
model1.solve()
model1.save("tipping_points_with_probability")
