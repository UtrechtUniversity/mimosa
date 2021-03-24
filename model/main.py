"""
Creates the class MIMOSA:
This is the main class. It builds a new AbstractModel
using the chosen damage and objective modules, then reads in the
parameter values and data (from the DataStore). With these values,
it creates an `instance` of the AbstractModel. This is then sent to the solver.
Finally, the export functions are called here.
"""

import os
import numpy as np

from model.common import (
    AbstractModel,
    TransformationFactory,
    SolverFactory,
    SolverManagerFactory,
    SolverStatus,
    value,
    OptSolver,
    data,
    regional_params,
    utils,
    units,
)
from model.export import full_plot, visualise_ipopt_output, save_output
from model.abstract_model import create_abstract_model

# Util to create a None-indexed dictionary for scalar components
# (see https://pyomo.readthedocs.io/en/stable/working_abstractmodels/data/raw_dicts.html)
V = lambda val: {None: val}


class MIMOSA:
    """
    The MIMOSA object creates an AbstractModel, makes a Concrete instance
    out of it, solves it and saves the results.

    Args:
        params (dict): contains all Param values, and is based on `input/config.yaml`

    Attributes:
        params (dict)
        regions (dict): taken from params
        quant (Quantity): callable object used to parse and convert quantities with units
        abstract_model (AbstractModel): the AbstractModel created using the chosen damage/objective modules
        data_store (DataStore): object used to access regional data from the input database
        m (ConcreteModel): concrete instance of `abstract_model`

    """

    def __init__(self, params: dict):
        self.params = params
        self.regions = params["regions"]
        self.quant = units.Quantity(params)

        self.abstract_model = self.get_abstract_model()
        self.m = self.create_instance()
        self.preparation()

    def get_abstract_model(self) -> AbstractModel:
        """
        Returns:
            AbstractModel: model corresponding to the damage/objective module combination
        """
        damage_module = self.params["model"]["damage module"]
        objective_module = self.params["model"]["objective module"]

        return create_abstract_model(damage_module, objective_module)

    @utils.timer("Concrete model creation")
    def create_instance(self):

        # Create the regional parameter store
        self.regional_param_store = regional_params.RegionalParamStore(self.params)

        # Create the data store
        self.data_store = data.DataStore(
            self.params, self.quant, self.regional_param_store
        )

        # The data functions need to be changed in the abstract model
        # before initialization.
        self.abstract_model.baseline_emissions = self.data_store.data_object("baseline")
        self.abstract_model.population = (
            self.abstract_model.L
        ) = self.data_store.data_object("population")
        self.abstract_model.GDP = self.data_store.data_object("GDP")
        self.abstract_model.carbon_intensity = self.data_store.data_object(
            "carbon_intensity"
        )
        self.abstract_model.TFP = self.data_store.data_object("TFP")

        damage_module = self.params["model"]["damage module"]

        instance_data = {None: {}}

        # Main instance data
        self._set_instance_data_main(instance_data)

        # Instance data for RICE2010 damage/adaptation:
        if damage_module == "RICE2010":
            self._set_instance_data_rice2010(instance_data)

        # Instance data for RICE2012 damage/adaptation:
        if damage_module == "RICE2012":
            self._set_instance_data_rice2012(instance_data)

        # Instance data for COACCH damages:
        if damage_module == "COACCH":
            self._set_instance_data_coacch(instance_data)

        # For WITCH damage/adaption:
        # if damage_module == "WITCH":
        #     instance_data[None].update(self._instance_data_witch())

        # Raise warning for partially irreversible damages when damage module != RICE2010:
        if (
            damage_module == "RICE2010"
            and self.params["economics"]["damages"]["percentage reversible"] != 1
        ):
            raise NotImplementedError(
                'Partially irreversible damages not implemented for damage module "{}"'.format(
                    damage_module
                )
            )

        m = self.abstract_model.create_instance(instance_data)
        return m

    def preparation(self) -> None:

        if len(self.regions) > 1:
            TransformationFactory("contrib.aggregate_vars").apply_to(self.m)
        TransformationFactory("contrib.init_vars_midpoint").apply_to(self.m)
        TransformationFactory("contrib.detect_fixed_vars").apply_to(self.m)
        if len(self.regions) > 1:
            TransformationFactory("contrib.propagate_fixed_vars").apply_to(self.m)

    @utils.timer("Model solve")
    def solve(
        self,
        verbose=False,
        halt_on_ampl_error="no",
        use_neos=False,
        neos_email=None,
        ipopt_output_file=None,
    ) -> None:
        if use_neos:
            os.environ["NEOS_EMAIL"] = neos_email
            solver_manager = SolverManagerFactory("neos")
            solver = "conopt"  # 'ipopt'
            results = solver_manager.solve(self.m, opt=solver)
        else:
            opt: OptSolver = SolverFactory("ipopt")
            opt.options["halt_on_ampl_error"] = halt_on_ampl_error
            opt.options["output_file"] = ipopt_output_file
            results = opt.solve(self.m, tee=verbose, symbolic_solver_labels=True)
            if ipopt_output_file is not None:
                visualise_ipopt_output(ipopt_output_file)

        # Restore aggregated variables
        if len(self.regions) > 1:
            TransformationFactory("contrib.aggregate_vars").update_variables(self.m)

        if results.solver.status != SolverStatus.ok:
            print(
                "Status: {}, termination condition: {}".format(
                    results.solver.status, results.solver.termination_condition
                )
            )
            if results.solver.status != SolverStatus.warning:
                raise Exception("Solver did not exit with status OK")

        print("Final NPV:", value(self.m.NPV[self.m.tf]))

    @utils.timer("Plotting results")
    def plot(self, filename="result", **kwargs):
        full_plot(self.m, filename, **kwargs)

    def save(self, experiment=None, **kwargs):
        save_output(self.params, self.m, experiment, **kwargs)

    ########################
    #
    # Private functions
    #
    ########################

    def _set_instance_data_main(self, instance_data) -> None:

        params = self.params
        quant = self.quant

        t_start = params["time"]["start"]
        t_end = params["time"]["end"]
        dt = params["time"]["dt"]
        num_years = int(np.ceil((t_end - t_start) / dt)) + 1
        self.abstract_model.year = lambda t: t_start + t * dt
        year2100 = int((2100 - t_start) / dt)

        parameter_mapping = {
            "beginyear": V(t_start),
            "dt": V(dt),
            "tf": V(num_years - 1),
            "t": V(range(num_years)),
            "year2100": V(year2100),
            "regions": V(params["regions"].keys()),
            "baseline_carbon_intensity": V(
                params["emissions"]["baseline carbon intensity"]
            ),
            "budget": V(quant(params["emissions"]["carbonbudget"], "emissions_unit")),
            "inertia_regional": V(params["emissions"]["inertia"]["regional"]),
            "inertia_global": V(params["emissions"]["inertia"]["global"]),
            "global_min_level": V(
                quant(params["emissions"]["global min level"], "emissionsrate_unit")
            ),
            "regional_min_level": V(
                quant(params["emissions"]["regional min level"], "emissionsrate_unit")
            ),
            "no_pos_emissions_after_budget_year": V(
                params["emissions"]["not positive after budget year"]
            ),
            "T0": V(quant(params["temperature"]["initial"], "temperature_unit")),
            "TCRE": V(
                quant(
                    params["temperature"]["TCRE"],
                    "(temperature_unit)/(emissions_unit)",
                )
            ),
            "LBD_rate": V(params["economics"]["MAC"]["rho"]),
            "LBD_scaling": V(quant("40 GtCO2", "emissions_unit")),
            "LOT_rate": V(0),
            "damage_scale_factor": V(params["economics"]["damages"]["scale factor"]),
            "fixed_adaptation": V(params["economics"]["adaptation"]["fixed"]),
            "perc_reversible_damages": V(
                params["economics"]["damages"]["percentage reversible"]
            ),
            "ignore_damages": V(params["economics"]["damages"]["ignore damages"]),
            "MAC_gamma": V(
                quant(
                    params["economics"]["MAC"]["gamma"],
                    "currency_unit/emissionsrate_unit",
                )
            ),
            "MAC_beta": V(params["economics"]["MAC"]["beta"]),
            "MAC_scaling_factor": self.regional_param_store.get("MAC", "kappa"),
            "init_capitalstock_factor": self.regional_param_store.get(
                "economics", "init_capital_factor"
            ),
            "alpha": V(params["economics"]["GDP"]["alpha"]),
            "dk": V(params["economics"]["GDP"]["depreciation of capital"]),
            "sr": V(params["economics"]["GDP"]["savings rate"]),
            "elasmu": V(params["economics"]["elasmu"]),
            "PRTP": V(params["economics"]["PRTP"]),
            "allow_trade": V(params["model"]["allow trade"]),
        }

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_rice2010(self, instance_data) -> None:
        params = self.params
        parameter_mapping = {
            "adapt_curr_level": V(params["economics"]["adaptation"]["curr_level"]),
            "damage_a1": self.regional_param_store.get("ADRICE2010", "a1"),
            "damage_a2": self.regional_param_store.get("ADRICE2010", "a2"),
            "damage_a3": self.regional_param_store.get("ADRICE2010", "a3"),
            "adapt_g1": self.regional_param_store.get("ADRICE2010", "g1"),
            "adapt_g2": self.regional_param_store.get("ADRICE2010", "g2"),
        }

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_rice2012(self, instance_data) -> None:
        parameter_mapping = {
            "damage_a1": self.regional_param_store.get("ADRICE2012", "a1"),
            "damage_a2": self.regional_param_store.get("ADRICE2012", "a2"),
            "damage_a3": self.regional_param_store.get("ADRICE2012", "a3"),
            "adap1": self.regional_param_store.get("ADRICE2012", "nu1"),
            "adap2": self.regional_param_store.get("ADRICE2012", "nu2"),
            "adap3": self.regional_param_store.get("ADRICE2012", "nu3"),
            "adapt_rho": V(0.5),
            "SLRdam1": self.regional_param_store.get("ADRICE2012", "slrdam1"),
            "SLRdam2": self.regional_param_store.get("ADRICE2012", "slrdam2"),
        }

        instance_data[None].update(parameter_mapping)

        # Set sea level rise parameters
        self._set_instance_data_rice2012_slr(instance_data)

    def _set_instance_data_rice2012_slr(self, instance_data) -> None:
        parameter_mapping = {
            # Sea level rise:
            "S1": V(0.5),
            "S2": V(0.0920666936642),
            "S3": V(0.024076141150722),
            "M1": V(0.0008),
            "M2": V(0.26),
            "M3": V(-1),
            "M4": V(1.11860081578514),
            "M5": V(0.6),
            "M6": V(7.3),
        }

        instance_data[None].update(parameter_mapping)

    def _set_instance_data_coacch(self, instance_data) -> None:
        # First, set sea level rise parameters from AD-RICE2012
        self._set_instance_data_rice2012_slr(instance_data)

        try:
            damage_quantile = self.params["economics"]["damages"]["quantile"]
        except KeyError:
            damage_quantile = 0.5

        slr_withadapt = self.params["economics"]["damages"]["coacch_slr_withadapt"]
        prfx = "SLR-Ad" if slr_withadapt else "SLR-NoAd"

        factor_noslr = f"NoSLR_a (q={damage_quantile})"
        factor_slr_ad = f"{prfx}_a (q={damage_quantile})"

        parameter_mapping = {
            # Non-SLR damages:
            "damage_noslr_form": self.regional_param_store.get("COACCH", "NoSLR_form"),
            "damage_noslr_b1": self.regional_param_store.get("COACCH", "NoSLR_b1"),
            "damage_noslr_b2": self.regional_param_store.get("COACCH", "NoSLR_b2"),
            "damage_noslr_b3": self.regional_param_store.get("COACCH", "NoSLR_b3"),
            "damage_noslr_a": self.regional_param_store.get("COACCH", factor_noslr),
            # SLR damages:
            "damage_slr_form": self.regional_param_store.get("COACCH", f"{prfx}_form"),
            "damage_slr_b1": self.regional_param_store.get("COACCH", f"{prfx}_b1"),
            "damage_slr_b2": self.regional_param_store.get("COACCH", f"{prfx}_b2"),
            "damage_slr_b3": self.regional_param_store.get("COACCH", f"{prfx}_b3"),
            "damage_slr_a": self.regional_param_store.get("COACCH", factor_slr_ad),
        }

        instance_data[None].update(parameter_mapping)

    # def _instance_data_witch(self) -> dict:
    #     return {
    #         "damage_omega1_pos": self.data_store.get_regional("damages", "omega1_pos"),
    #         "damage_omega1_neg": self.data_store.get_regional("damages", "omega1_neg"),
    #         "damage_omega2_pos": self.data_store.get_regional("damages", "omega2_pos"),
    #         "damage_omega2_neg": self.data_store.get_regional("damages", "omega2_neg"),
    #         "damage_omega3_pos": self.data_store.get_regional("damages", "omega3_pos"),
    #         "damage_omega3_neg": self.data_store.get_regional("damages", "omega3_neg"),
    #         "damage_omega4_pos": self.data_store.get_regional("damages", "omega4_pos"),
    #         "damage_omega4_neg": self.data_store.get_regional("damages", "omega4_neg"),
    #         "adapt_omega_eff_ada": self.data_store.get_regional(
    #             "adaptation", "omega_eff_ada"
    #         ),
    #         "adapt_omega_act": self.data_store.get_regional("adaptation", "omega_act"),
    #         "adapt_omega_eff_act": self.data_store.get_regional(
    #             "adaptation", "omega_eff_act"
    #         ),
    #         "adapt_omega_rada": self.data_store.get_regional(
    #             "adaptation", "omega_rada"
    #         ),
    #         "adapt_rho_ada": self.data_store.get_regional("adaptation", "rho_ada"),
    #         "adapt_rho_act": self.data_store.get_regional("adaptation", "rho_act"),
    #         "adapt_eps": self.data_store.get_regional("adaptation", "eps"),
    #     }
