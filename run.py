from mimosa import MIMOSA, load_params
from numpy import random

# First run MIMOSA in optimisation mode

params = load_params()
params["time"]["end"] = 2300
params["emissions"]["non increasing emissions after 2100"] = False

# Values are from Deutloff et al. (2025)
# and can be accessed in the file "Code/Read Data/Constants_new.py"
# from Deutloff's published code
AMAZ_sample = random.lognormal(mean=1.25, sigma=0.33, size=1000)
AMOC_sample = random.triangular(left=0.36, mode=2.64, right=9.85, size=1000)
LABC_sample = random.lognormal(mean=0.59, sigma=0.33, size=1000)
PFAT_sample = random.lognormal(mean=0.41, sigma=0.25, size=1000)

AMAZ_tipping_temp = random.choice(AMAZ_sample)
AMOC_tipping_temp = random.choice(AMOC_sample)
LABC_tipping_temp = random.choice(LABC_sample)
PFAT_tipping_temp = random.choice(PFAT_sample)

params["model structure"]["tippingpoints options"]["include ALL"] = True

params["tippingpoints"]["AMAZ"]["threshold"] = AMAZ_tipping_temp
params["tippingpoints"]["AMOC"]["threshold"] = AMOC_tipping_temp
params["tippingpoints"]["LABC"]["threshold"] = LABC_tipping_temp
params["tippingpoints"]["PFAT"]["threshold"] = PFAT_tipping_temp


model1 = MIMOSA(params)
model1.solve()
model1.save("CDF_thresholds_run5")
