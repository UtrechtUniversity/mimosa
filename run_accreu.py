import logging
import logging.handlers
import pandas as pd

from mimosa import MIMOSA, load_params

handler = logging.handlers.WatchedFileHandler("accreu.log")
handler.setFormatter(
    logging.Formatter("[%(levelname)s, %(asctime)s] %(name)s - %(message)s")
)
root = logging.getLogger()
root.setLevel("INFO")
root.addHandler(handler)

PREFIX = "accreu"

adaptation_readiness = pd.read_csv("data/adaptation_readiness.csv").set_index(
    ["SSP", "Region"]
)


def init_params(adaptation_type, monetise_mortality):
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    params["model structure"]["damage module options"][
        "ACCREU adaptation"
    ] = adaptation_type
    params["model structure"]["damage module options"][
        "ACCREU_monetise_mortality"
    ] = monetise_mortality
    return params


def reduce_adaptation_costs(ssp, concrete_model):
    adaptation_vars = [
        "labourprod_adaptation_costs_abs",
        "slr_adaptation_costs_abs",
        "riverine_adaptation_costs_abs",
    ]

    control_values = {
        "relative_abatement": concrete_model.relative_abatement.extract_values()
    }

    def _get_adapt_readiness(t, r):
        year = str(int(concrete_model.year(t)))
        return adaptation_readiness.loc[(ssp, r), year]

    for adapt_var in adaptation_vars:
        values = getattr(concrete_model, adapt_var).extract_values()
        # Reduce these values by the adaptation readiness in each year/region
        reduced_values = {
            (t, r): _get_adapt_readiness(t, r) * value
            for (t, r), value in values.items()
        }
        control_values[adapt_var] = reduced_values

    return control_values


for monetise_mortality in [False, True]:

    #### Run "mit": CBA with no adaptation
    params_mit = init_params("noadaptation", monetise_mortality)
    model_mit = MIMOSA(params_mit)
    model_mit.solve()
    model_mit.save(f"{PREFIX}_mit_mortality_{monetise_mortality}")

    #### Run "baseline": no-policy baseline with no adaptation
    params_baseline = init_params("noadaptation", monetise_mortality)
    model_baseline = MIMOSA(params_baseline)
    sim_run_baseline = model_baseline.run_nopolicy_baseline()
    model_baseline.save_simulation(
        sim_run_baseline, f"{PREFIX}_baseline_mortality_{monetise_mortality}"
    )

    for adaptation_type in ["separate"]:  # "separate", "combined"

        #### Run "ada": no-policy baseline with optimal adaptation
        params_ada = init_params(adaptation_type, monetise_mortality)
        params_ada["model structure"]["damage module options"][
            "ACCREU_adaptation_impose_optimal"
        ] = True
        model_ada = MIMOSA(params_ada)
        sim_ada = model_ada.run_nopolicy_baseline()
        model_ada.save_simulation(
            sim_ada,
            f"{PREFIX}_ada_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )

        #### Run "mit_then_ada": Given mitigation from run mit, optimise adaptation
        params_mit_then_ada = init_params(adaptation_type, monetise_mortality)
        params_mit_then_ada["model structure"]["damage module options"][
            "ACCREU_adaptation_impose_optimal"
        ] = True
        relative_abatement_mit = (
            model_mit.concrete_model.relative_abatement.extract_values()
        )
        model_mit_then_ada = MIMOSA(params_mit_then_ada)
        sim_mit_then_ada = model_mit_then_ada.run_simulation(
            relative_abatement=relative_abatement_mit
        )
        model_mit_then_ada.save_simulation(
            sim_mit_then_ada,
            f"{PREFIX}_mit_then_ada_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )

        #### Run "ada_unplanned": Take the adaptation-only run and just change the adaptation level
        params_ada_unplanned = init_params(adaptation_type, monetise_mortality)
        params_ada_unplanned["economics"]["damages"]["accreu"][
            "adaptation_effectiveness_scale_factor"
        ] = 0.5
        model_ada_unplanned = MIMOSA(params_ada_unplanned)

        control_variables = model_ada_unplanned.simulator.control_variables
        control_variables_values = {
            var: getattr(sim_ada, var).extract_values() for var in control_variables
        }
        sim_ada_unplanned = model_ada_unplanned.run_simulation(
            **control_variables_values
        )
        model_ada_unplanned.save_simulation(
            sim_ada_unplanned,
            f"{PREFIX}_ada_unplanned_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )

        #### Run "ada_planned": Take a MIMOSA optimisation run and reduce the optimal adaptation level by the readiness factor
        params_ada_planned = init_params(adaptation_type, monetise_mortality)
        model_ada_planned = MIMOSA(params_ada_planned)

        reduced_control_variables_values = reduce_adaptation_costs(
            params_ada_planned["SSP"], sim_ada
        )
        sim_ada_planned = model_ada_planned.run_simulation(
            **reduced_control_variables_values
        )
        model_ada_planned.save_simulation(
            sim_ada_planned,
            f"{PREFIX}_ada_planned_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )

        #### Run "mit_ada": CBA with adaptation optimised by MIMOSA
        params_mit_ada = init_params(adaptation_type, monetise_mortality)
        model_mit_ada = MIMOSA(params_mit_ada)
        model_mit_ada.solve(ipopt_maxiter=10000)
        model_mit_ada.save(
            f"{PREFIX}_mit_ada_adapt_{adaptation_type}_mortality_{monetise_mortality}"
        )

        # #### Run "mit_ada_unplanned": Take a MIMOSA optimisation run and just change the adaptation level
        # params_mit_ada_unplanned = init_params(adaptation_type, monetise_mortality)
        # params_mit_ada_unplanned["economics"]["damages"]["accreu"][
        #     "adaptation_effectiveness_scale_factor"
        # ] = 0.5
        # model_mit_ada_unplanned = MIMOSA(params_mit_ada_unplanned)

        # control_variables = model_mit_ada.simulator.control_variables
        # control_variables_values = {
        #     var: getattr(model_mit_ada.concrete_model, var).extract_values()
        #     for var in control_variables
        # }
        # sim_mit_ada_unplanned = model_mit_ada_unplanned.run_simulation(
        #     **control_variables_values
        # )
        # model_mit_ada_unplanned.save_simulation(
        #     sim_mit_ada_unplanned,
        #     f"{PREFIX}_mit_ada_unplanned_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        # )

        # #### Run "mit_ada_planned": Take a MIMOSA optimisation run and reduce the optimal adaptation level by the readiness factor
        # params_mit_ada_planned = init_params(adaptation_type, monetise_mortality)
        # model_mit_ada_planned = MIMOSA(params_mit_ada_planned)

        # reduced_control_variables_values = reduce_adaptation_costs(params_mit_ada_planned["SSP", model_mit_ada.concrete_model)
        # sim_mit_ada_planned = model_mit_ada_planned.run_simulation(
        #     **reduced_control_variables_values
        # )
        # model_mit_ada_planned.save_simulation(
        #     sim_mit_ada_planned,
        #     f"{PREFIX}_mit_ada_planned_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        # )
