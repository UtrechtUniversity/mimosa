import logging
import logging.handlers
import pandas as pd

from mimosa import MIMOSA, load_params

log_file = "accreu.log"

# Add blank line to log file for easier debug:
with open(log_file, "a") as f:
    f.write("\n")


handler = logging.handlers.WatchedFileHandler(log_file)
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


def init_params(monetise_mortality, adapt_calibration="accreu", adapt_type="separate"):
    params = load_params()
    params["model structure"]["damage module"] = "ACCREU"
    params["model structure"]["damage module options"][
        "ACCREU_adaptation"
    ] = adapt_type  # "separate" or "combined"
    params["model structure"]["damage module options"][
        "ACCREU_monetise_mortality"
    ] = monetise_mortality
    params["model structure"]["damage module options"][
        "ACCREU_adaptation_calibration"
    ] = adapt_calibration  # "accreu", "literature", "literature_low", "literature_high"
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
    params_mit = init_params(monetise_mortality, adapt_type="noadaptation")
    model_mit = MIMOSA(params_mit)
    model_mit.solve()
    model_mit.save(f"{PREFIX}_mit_mortality_{monetise_mortality}")

    #### Run "baseline": no-policy baseline with no adaptation
    params_baseline = init_params(monetise_mortality, adapt_type="noadaptation")
    model_baseline = MIMOSA(params_baseline)
    sim_run_baseline = model_baseline.run_nopolicy_baseline()
    model_baseline.save_simulation(
        sim_run_baseline, f"{PREFIX}_baseline_mortality_{monetise_mortality}"
    )

    for adapt_calibration in [
        "accreu",
        "literature",
        "literature_low",
        "literature_high",
    ]:

        #### Run "ada": no-policy baseline with optimal adaptation
        params_ada = init_params(monetise_mortality, adapt_calibration)
        model_ada = MIMOSA(params_ada)
        sim_ada = model_ada.run_nopolicy_baseline()
        model_ada.save_simulation(
            sim_ada,
            f"{PREFIX}_ada_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}",
        )

        #### Run "mit_then_ada": optimise mitigation, then calculate adaptation
        params_mit_then_ada = init_params(monetise_mortality, adapt_calibration)
        model_mit_then_ada = MIMOSA(params_mit_then_ada)
        model_mit_then_ada.solve()
        model_mit_then_ada.save(
            f"{PREFIX}_mit_then_ada_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}",
        )

        #### Run "ada_unplanned": Take the adaptation-only run and just change the adaptation level. The adaptation is therefore less effective then originally thought.
        params_ada_unplanned = init_params(monetise_mortality, adapt_calibration)
        params_ada_unplanned["economics"]["damages"]["accreu"][
            "adaptation_effectiveness_scale_factor"
        ] = 0.5
        params_ada_unplanned["model structure"]["damage module options"][
            "ACCREU_CBA_strategy"
        ] = "joint"
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
            f"{PREFIX}_ada_unplanned_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}",
        )

        #### Run "ada_planned": Take a MIMOSA optimisation run and reduce the optimal adaptation level by the
        # adaptation readiness factor (dependent on governance/institutional/socio-economic factors). Countries therefore
        # have to spend less than the optimal amount, because they are unable to implement all the optimal adaptation
        # measures. The resulting reduced damages are lower, but that's because the adaptation costs are lower.
        # In ada_unplanned the adaptation costs are the same as optimal adaptation, just the effectiveness is reduced.
        params_ada_planned = init_params(monetise_mortality, adapt_calibration)
        params_ada_planned["model structure"]["damage module options"][
            "ACCREU_CBA_strategy"
        ] = "joint"
        model_ada_planned = MIMOSA(params_ada_planned)

        reduced_control_variables_values = reduce_adaptation_costs(
            params_ada_planned["SSP"], sim_ada
        )
        sim_ada_planned = model_ada_planned.run_simulation(
            **reduced_control_variables_values
        )
        model_ada_planned.save_simulation(
            sim_ada_planned,
            f"{PREFIX}_ada_planned_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}",
        )

        #### Run "mit_ada": CBA with mitigation and adaptation optimised at the same time by MIMOSA
        params_mit_ada = init_params(monetise_mortality, adapt_calibration)
        params_mit_ada["model structure"]["damage module options"][
            "ACCREU_CBA_strategy"
        ] = "joint"
        model_mit_ada = MIMOSA(params_mit_ada)
        model_mit_ada.solve(ipopt_maxiter=10000)
        model_mit_ada.save(
            f"{PREFIX}_mit_ada_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}"
        )

        # #### Run "mit_ada_unplanned": Take a MIMOSA optimisation run and just change the adaptation level
        # params_mit_ada_unplanned = init_params(monetise_mortality, adapt_calibration)
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
        #     f"{PREFIX}_mit_ada_unplanned_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}",
        # )

        # #### Run "mit_ada_planned": Take a MIMOSA optimisation run and reduce the optimal adaptation level by the readiness factor
        # params_mit_ada_planned = init_params(monetise_mortality, adapt_calibration)
        # model_mit_ada_planned = MIMOSA(params_mit_ada_planned)

        # reduced_control_variables_values = reduce_adaptation_costs(params_mit_ada_planned["SSP", model_mit_ada.concrete_model)
        # sim_mit_ada_planned = model_mit_ada_planned.run_simulation(
        #     **reduced_control_variables_values
        # )
        # model_mit_ada_planned.save_simulation(
        #     sim_mit_ada_planned,
        #     f"{PREFIX}_mit_ada_planned_adapt_calib_{adapt_calibration}_mortality_{monetise_mortality}",
        # )
