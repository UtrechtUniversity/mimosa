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

ERROR_FILE = "log_dmg_target.txt"


def do_run(
    new_params,
    budget,
    TCRE,
    perc,
    gamma,
    r,
    min_level,
    damage_coeff,
    damage_target=False,
    elasmu=1.001,
):
    new_params["economics"]["PRTP"] = r
    new_params["economics"]["elasmu"] = elasmu
    new_params["economics"]["MAC"]["gamma"] = f"{gamma} USD2005/tCO2"
    new_params["regions"]["WorldOrig"]["damages"]["a2"] = damage_coeff
    new_params["emissions"]["min level"] = min_level
    new_params["economics"]["damages"]["percentage reversible"] = perc
    new_params["economics"]["damages"]["target"] = damage_target
    new_params["temperature"]["TCRE"] = TCRE
    new_params["emissions"]["carbonbudget"] = (
        "{} GtCO2".format(budget) if budget is not False else False
    )
    try:
        model = MIMOSA(new_params)
        model.solve(verbose=True)
        model.save("netnegs", folder="output/netnegsResubmissionDamageTargetNewBurke")
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


def damage(temperature, init_temperature, coeff):
    return float(coeff) * (temperature ** 2 - init_temperature ** 2)


def calc_damage_target(carbonbudget, damage_coeff, params, tcre=0.00062):
    init_temperature = float(params["temperature"]["initial"].split(" ")[0])
    end_of_century_temperature = init_temperature + tcre * carbonbudget
    return damage(end_of_century_temperature, init_temperature, damage_coeff)


### RUNS FOR FIGURE 3
# for min_level in ["-20 GtCO2/yr"]:
#     for gamma in [gamma_p50, gamma_p05, gamma_p95]:
#         for damage_coeff in damage_coeffs:
#             for PRTP in [0.015, 0.001, 0.03]:
#                 for perc in [1.0]:  # np.linspace(0.9, 0, 10):
#                     new_params = dict(nonegs_params)
#                     damage_target = calc_damage_target(600, damage_coeff, new_params)
#                     do_run(
#                         new_params,
#                         False,
#                         "0.62 delta_degC/(TtCO2)",
#                         perc,
#                         gamma,
#                         PRTP,
#                         min_level,
#                         damage_coeff,
#                         damage_target=damage_target,
#                     )

# Singles:
# for budget, perc, gamma, r, min_level, damage_coeff in [
# ]:
#     new_params = dict(nonegs_params)
#     new_params["time"]["dt"] = 1
#     new_params["time"]["end"] = 2150
#     damage_target = calc_damage_target(600, damage_coeff, new_params)
#     do_run(
#         new_params,
#         budget,
#         "0.62 delta_degC/(TtCO2)",
#         perc,
#         gamma,
#         r,
#         min_level,
#         damage_coeff,
#         damage_target=damage_target,
#     )

