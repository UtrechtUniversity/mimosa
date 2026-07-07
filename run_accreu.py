import logging
import logging.handlers

from mimosa import MIMOSA, load_params

handler = logging.handlers.WatchedFileHandler("accreu.log")
handler.setFormatter(
    logging.Formatter("[%(levelname)s, %(asctime)s] %(name)s - %(message)s")
)
root = logging.getLogger()
root.setLevel("INFO")
root.addHandler(handler)


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


for monetise_mortality in [True, False]:

    #### Run "mit" (Tier 1): CBA with no adaptation
    params_mit = init_params("noadaptation", monetise_mortality)
    model_mit = MIMOSA(params_mit)
    model_mit.solve()
    model_mit.save(f"accreu_tier1_mit_mortality_{monetise_mortality}")

    #### Run "baseline" (Tier 1): no-policy baseline with no adaptation
    params_baseline = init_params("noadaptation", monetise_mortality)
    model_baseline = MIMOSA(params_baseline)
    sim_run_baseline = model_baseline.run_nopolicy_baseline()
    model_baseline.save_simulation(
        sim_run_baseline, f"accreu_tier1_baseline_mortality_{monetise_mortality}"
    )

    for adaptation_type in ["combined", "separate"]:

        #### Run "mit_ada" (Tier 1): CBA with adaptation optimised by MIMOSA
        params_mit_ada = init_params(adaptation_type, monetise_mortality)
        model_mit_ada = MIMOSA(params_mit_ada)
        model_mit_ada.solve(ipopt_maxiter=10000)
        model_mit_ada.save(
            f"accreu_tier1_mit_ada_adapt_{adaptation_type}_mortality_{monetise_mortality}"
        )

        #### Run "ada" (Tier 1): no-policy baseline with optimal adaptation
        params_ada = init_params(adaptation_type, monetise_mortality)
        params_ada["model structure"]["damage module options"][
            "ACCREU_adaptation_impose_optimal"
        ] = True
        model_ada = MIMOSA(params_ada)
        sim_ada = model_ada.run_nopolicy_baseline()
        model_ada.save_simulation(
            sim_ada,
            f"accreu_tier1_ada_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )

        #### Run "mit_then_ada" (Tier 4): Given mitigation from run mit, optimise adaptation
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
            f"accreu_tier4_mit_then_ada_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )

        #### Run "mit_ada_unplanned" (Tier 2): Take a MIMOSA optimisation run and just change the adaptation level
        params_mit_ada_unplanned = init_params(adaptation_type, monetise_mortality)
        params_mit_ada_unplanned["economics"]["damages"]["accreu"][
            "adaptation_effectiveness_scale_factor"
        ] = 0.5
        model_mit_ada_unplanned = MIMOSA(params_mit_ada_unplanned)

        control_variables = model_mit_ada.simulator.control_variables
        control_variables_values = {
            var: getattr(model_mit_ada.concrete_model, var).extract_values()
            for var in control_variables
        }
        sim_mit_ada_unplanned = model_mit_ada_unplanned.run_simulation(
            **control_variables_values
        )
        model_mit_ada_unplanned.save_simulation(
            sim_mit_ada_unplanned,
            f"accreu_tier2_mit_ada_unplanned_adapt_{adaptation_type}_mortality_{monetise_mortality}",
        )
