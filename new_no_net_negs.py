import numpy as np
from datetime import datetime
from model.main import MIMOSA

COEFF_DICE = 0.00267
COEFF_HOWARD = 0.010038
COEFF_BURKE = 0.0283483

gamma_p05 = 954.9608
gamma_p50 = 2442.3716
gamma_p95 = 5996.4614

from model.common.config import params

nonegs_params = dict(params)
nonegs_params["regions"] = {
    "WorldOrig": {
        "initial capital": "223 trillion US$2005/yr",
        "damages": {"a1": 0, "a2": COEFF_DICE, "a3": 2},
        "adaptation": {"g1": 0.115, "g2": 3.6},
    }
}
nonegs_params["model"]["damage module"] = "RICE2010"
nonegs_params["time"] = {"start": 2020, "end": 2150, "dt": 1}
nonegs_params["economics"]["adaptation"]["curr_level"] = 0
nonegs_params["economics"]["adaptation"]["fixed"] = True
nonegs_params["emissions"]["inertia"]["regional"] = -0.0506

ERROR_FILE = "log.txt"


def do_run(
    new_params, budget, TCRE, perc, gamma, r, min_level, damage_coeff, elasmu=1.001
):
    new_params["economics"]["PRTP"] = r
    new_params["economics"]["elasmu"] = elasmu
    new_params["economics"]["MAC"]["gamma"] = f"{gamma} USD2005/tCO2"
    new_params["regions"]["WorldOrig"]["damages"]["a2"] = damage_coeff
    new_params["emissions"]["min level"] = min_level
    new_params["economics"]["damages"]["percentage reversible"] = perc
    new_params["temperature"]["TCRE"] = TCRE
    new_params["emissions"]["carbonbudget"] = (
        "{} GtCO2".format(budget) if budget is not False else False
    )
    try:
        model = MIMOSA(new_params)
        model.solve(verbose=True)
        model.save("netnegs", folder="output/netnegsResubmissionNewBurke")
    except:
        print("============================")
        print(
            "Error with budget={}, TCRE={}, perc={}, gamma={}, r={}, min_level={}, damage={}".format(
                budget, TCRE, perc, gamma, r, min_level, damage_coeff
            )
        )
        with open(ERROR_FILE, "a") as fh:
            fh.write(
                "{}, # {}\n".format(
                    [budget, TCRE, perc, gamma, r, min_level, damage_coeff],
                    datetime.now(),
                )
            )
        print("============================")


damage_coeffs = np.linspace(0.00267, 0.0283483, 7)


### RUNS FOR FIGURE 1 AND 2
# for budget in [600, 1344]:
#     for TCRE in [
#         "0.62 delta_degC/(TtCO2)",
#         "0.42 delta_degC/(TtCO2)",
#         "0.82 delta_degC/(TtCO2)",
#     ]:
#         for perc in [1]:
#             for gamma in [gamma_p50, gamma_p05, gamma_p95]:
#                 for r in [0.001, 0.015, 0.03]:
#                     for min_level in ["-20 GtCO2/yr", "0 GtCO2/yr"]:
#                         if min_level == "0 GtCO2/yr" and perc != 1:
#                             continue
#                         for damage_coeff in damage_coeffs:
#                             new_params = dict(nonegs_params)
#                             do_run(
#                                 new_params,
#                                 budget,
#                                 TCRE,
#                                 perc,
#                                 gamma,
#                                 r,
#                                 min_level,
#                                 damage_coeff,
#                             )


# for budget, TCRE, perc, gamma, r, min_level, damage_coeff in [
# ]:
#     new_params = dict(nonegs_params)
#     new_params["time"]["dt"] = 1
#     new_params["time"]["end"] = 2155
#     do_run(
#         new_params, budget, TCRE, perc, gamma, r, min_level, damage_coeff,
#     )

### RUNS FOR FIGURE 3
# for gamma in [gamma_p05, gamma_p95, gamma_p50]:
#     for damage_coeff in damage_coeffs:
#         for PRTP in [0.001, 0.015, 0.03]:
#             for perc in np.linspace(0.9, 0, 10):
#                 new_params = dict(nonegs_params)
#                 do_run(
#                     new_params,
#                     600,
#                     "0.62 delta_degC/(TtCO2)",
#                     perc,
#                     gamma,
#                     PRTP,
#                     "-20 GtCO2/yr",
#                     damage_coeff,
#                 )
