from mimosa import MIMOSA, load_params
from numpy import random

# First run MIMOSA in optimisation mode

params = load_params()
params["time"]["end"] = 2300
params["time"]["periods"] = {2050: 10, 2100: 20}
params["emissions"]["non increasing emissions after 2100"] = False


for i in range(0, 20):

    # values are from Deutloff et al. (2025)
    # and can be accessed in the file "Code/Read Data/Constants_new.py" from Deutloff's published code
    AMAZ_tipping_temp = random.lognormal(mean=1.25, sigma=0.33, size=1)
    AMOC_tipping_temp = random.triangular(left=0.36, mode=2.64, right=9.85, size=1)
    AWSI_tipping_temp = random.lognormal(mean=1.84, sigma=0.20, size=1)
    LABC_tipping_temp = random.lognormal(mean=0.59, sigma=0.33, size=1)
    PFAT_tipping_temp = random.lognormal(mean=0.41, sigma=0.25, size=1)

    params["model structure"]["tippingpoints options"]["include ALL"] = True

    params["tippingpoints"]["AMAZ"]["threshold"] = AMAZ_tipping_temp[0]
    params["tippingpoints"]["AMOC"]["threshold"] = AMOC_tipping_temp[0]
    params["tippingpoints"]["AWSI"]["threshold"] = AWSI_tipping_temp[0]
    params["tippingpoints"]["LABC"]["threshold"] = LABC_tipping_temp[0]
    params["tippingpoints"]["PFAT"]["threshold"] = PFAT_tipping_temp[0]

    model1 = MIMOSA(params)
    model1.solve()
    model1.save("run_17_09_2026_" + str(i))



# for single runs
"""
AMAZ_tipping_temp = random.lognormal(mean=1.25, sigma=0.33, size=1)
AMOC_tipping_temp = random.triangular(left=0.36, mode=2.64, right=9.85, size=1)
AWSI_tipping_temp = random.lognormal(mean=1.84, sigma=0.20, size=1)
LABC_tipping_temp = random.lognormal(mean=0.59, sigma=0.33, size=1)
PFAT_tipping_temp = random.lognormal(mean=0.41, sigma=0.25, size=1)

params["model structure"]["tippingpoints options"]["include ALL"] = True

params["tippingpoints"]["AMAZ"]["threshold"] = AMAZ_tipping_temp[0]
params["tippingpoints"]["AMOC"]["threshold"] = AMOC_tipping_temp[0]
params["tippingpoints"]["AWSI"]["threshold"] = AWSI_tipping_temp[0]
params["tippingpoints"]["LABC"]["threshold"] = LABC_tipping_temp[0]
params["tippingpoints"]["PFAT"]["threshold"] = PFAT_tipping_temp[0]

model1 = MIMOSA(params)
model1.solve()
model1.save("new_PFAT_calculation")
"""