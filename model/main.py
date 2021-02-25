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

from model.common import data, utils, units
from model.common.pyomo import (
    TransformationFactory,
    SolverFactory,
    SolverManagerFactory,
    SolverStatus,
    value,
)
from model.export.plot import full_plot, visualise_IPOPT_output
from model.export.save import save_output

from model.abstract_model import create_abstract_model

ABSTRACT_MODELS = {}


class MIMOSA:
    def __init__(self, params):
        self.params = params
        self.regions = params["regions"]
        self.quant = units.Quantity(params)

        self.abstract_model = self.get_abstract_model()
        self.m = self.create_instance()
        self.preparation()

    def get_abstract_model(self):
        damage_module = self.params["model"]["damage module"]
        objective_module = self.params["model"]["objective module"]
        if (damage_module, objective_module) not in ABSTRACT_MODELS:
            ABSTRACT_MODELS[(damage_module, objective_module)] = create_abstract_model(
                damage_module, objective_module
            )

        return ABSTRACT_MODELS[(damage_module, objective_module)]

    @utils.timer("Concrete model creation")
    def create_instance(self):

        # Create the data store
        self.data_store = data.DataStore(self.params, self.quant)

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

        quant = self.quant
        params = self.params

        t_start = params["time"]["start"]
        t_end = params["time"]["end"]
        dt = params["time"]["dt"]
        num_years = int(np.ceil((t_end - t_start) / dt)) + 1
        self.abstract_model.year = lambda t: t_start + t * dt
        year2100 = int((2100 - t_start) / dt)

        # Util to create a None-indexed dictionary for scalar components
        # (see https://pyomo.readthedocs.io/en/stable/working_abstractmodels/data/raw_dicts.html)
        v = lambda val: {None: val}

        instance_data = {
            None: {
                "beginyear": v(t_start),
                "dt": v(dt),
                "tf": v(num_years - 1),
                "t": v(range(num_years)),
                "year2100": v(year2100),
                "regions": v(params["regions"].keys()),
                "baseline_carbon_intensity": v(
                    params["emissions"]["baseline carbon intensity"]
                ),
                "budget": v(
                    quant(params["emissions"]["carbonbudget"], "emissions_unit")
                ),
                "inertia_regional": v(params["emissions"]["inertia"]["regional"]),
                "inertia_global": v(params["emissions"]["inertia"]["global"]),
                "global_min_level": v(
                    quant(params["emissions"]["global min level"], "emissionsrate_unit")
                ),
                "regional_min_level": v(
                    quant(
                        params["emissions"]["regional min level"], "emissionsrate_unit"
                    )
                ),
                "no_pos_emissions_after_budget_year": v(
                    params["emissions"]["not positive after budget year"]
                ),
                "T0": v(quant(params["temperature"]["initial"], "temperature_unit")),
                "TCRE": v(
                    quant(
                        params["temperature"]["TCRE"],
                        "(temperature_unit)/(emissions_unit)",
                    )
                ),
                "LBD_rate": v(params["economics"]["MAC"]["rho"]),
                "LBD_scaling": v(quant("40 GtCO2", "emissions_unit")),
                "LOT_rate": v(0),
                "damage_scale_factor": v(
                    params["economics"]["damages"]["scale factor"]
                ),
                "fixed_adaptation": v(params["economics"]["adaptation"]["fixed"]),
                "perc_reversible_damages": v(
                    params["economics"]["damages"]["percentage reversible"]
                ),
                "ignore_damages": v(params["economics"]["damages"]["ignore damages"]),
                "MAC_gamma": v(
                    quant(
                        params["economics"]["MAC"]["gamma"],
                        "currency_unit/emissionsrate_unit",
                    )
                ),
                "MAC_beta": v(params["economics"]["MAC"]["beta"]),
                "MAC_scaling_factor": {
                    r: self.regions[r]["MAC scaling factor"] for r in self.regions
                },
                "init_capitalstock_factor": {
                    r: self.regions[r]["initial capital factor"] for r in self.regions
                },
                "alpha": v(params["economics"]["GDP"]["alpha"]),
                "dk": v(params["economics"]["GDP"]["depreciation of capital"]),
                "sr": v(params["economics"]["GDP"]["savings rate"]),
                "elasmu": v(params["economics"]["elasmu"]),
                "PRTP": v(params["economics"]["PRTP"]),
                "allow_trade": v(params["model"]["allow trade"]),
            }
        }

        # For RICE2010 damage/adaptation:
        if params["model"]["damage module"] == "RICE2010":
            instance_data[None].update(
                {
                    "adapt_curr_level": v(
                        params["economics"]["adaptation"]["curr_level"]
                    ),
                    "damage_a1": self.data_store.get_regional("damages", "a1"),
                    "damage_a2": self.data_store.get_regional("damages", "a2"),
                    "damage_a3": self.data_store.get_regional("damages", "a3"),
                    "adapt_g1": self.data_store.get_regional("adaptation", "g1"),
                    "adapt_g2": self.data_store.get_regional("adaptation", "g2"),
                }
            )
        elif params["economics"]["damages"]["percentage reversible"] != 1:
            raise NotImplementedError(
                'Partially irreversible damages not implemented for damage module "{}"'.format(
                    params["model"]["damage module"]
                )
            )

        # For RICE2012 damage/adaptation:
        if params["model"]["damage module"] == "RICE2012":
            instance_data[None].update(
                {
                    "adapt_curr_level": v(
                        params["economics"]["adaptation"]["curr_level"]
                    ),
                    "damage_a1": self.data_store.get_regional("damages", "a1"),
                    "damage_a2": self.data_store.get_regional("damages", "a2"),
                    "damage_a3": self.data_store.get_regional("damages", "a3"),
                    "adap1": self.data_store.get_regional("adaptation", "nu1"),
                    "adap2": self.data_store.get_regional("adaptation", "nu2"),
                    "adap3": self.data_store.get_regional("adaptation", "nu3"),
                    "adapt_rho": v(0.5),
                    # Sea level rise:
                    "S1": v(0.5),
                    "S2": v(0.0920666936642),
                    "S3": v(0.024076141150722),
                    "M1": v(0.0008),
                    "M2": v(0.26),
                    "M3": v(-1),
                    "M4": v(1.11860081578514),
                    "M5": v(0.6),
                    "M6": v(7.3),
                    "SLRdam1": self.data_store.get_regional("damages", "SLRDAM1"),
                    "SLRdam2": self.data_store.get_regional("damages", "SLRDAM2"),
                }
            )

        # For WITCH damage/adaption:
        if params["model"]["damage module"] == "WITCH":
            instance_data[None].update(
                {
                    "damage_omega1_pos": self.data_store.get_regional(
                        "damages", "omega1_pos"
                    ),
                    "damage_omega1_neg": self.data_store.get_regional(
                        "damages", "omega1_neg"
                    ),
                    "damage_omega2_pos": self.data_store.get_regional(
                        "damages", "omega2_pos"
                    ),
                    "damage_omega2_neg": self.data_store.get_regional(
                        "damages", "omega2_neg"
                    ),
                    "damage_omega3_pos": self.data_store.get_regional(
                        "damages", "omega3_pos"
                    ),
                    "damage_omega3_neg": self.data_store.get_regional(
                        "damages", "omega3_neg"
                    ),
                    "damage_omega4_pos": self.data_store.get_regional(
                        "damages", "omega4_pos"
                    ),
                    "damage_omega4_neg": self.data_store.get_regional(
                        "damages", "omega4_neg"
                    ),
                    "adapt_omega_eff_ada": self.data_store.get_regional(
                        "adaptation", "omega_eff_ada"
                    ),
                    "adapt_omega_act": self.data_store.get_regional(
                        "adaptation", "omega_act"
                    ),
                    "adapt_omega_eff_act": self.data_store.get_regional(
                        "adaptation", "omega_eff_act"
                    ),
                    "adapt_omega_rada": self.data_store.get_regional(
                        "adaptation", "omega_rada"
                    ),
                    "adapt_rho_ada": self.data_store.get_regional(
                        "adaptation", "rho_ada"
                    ),
                    "adapt_rho_act": self.data_store.get_regional(
                        "adaptation", "rho_act"
                    ),
                    "adapt_eps": self.data_store.get_regional("adaptation", "eps"),
                }
            )

        m = self.abstract_model.create_instance(instance_data)
        return m

    def preparation(self):

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
        use_NEOS=False,
        NEOS_EMAIL=None,
        IPOPT_output_file=None,
    ):
        if use_NEOS:
            os.environ["NEOS_EMAIL"] = NEOS_EMAIL
            solver_manager = SolverManagerFactory("neos")
            solver = "conopt"  # 'ipopt'
            results = solver_manager.solve(self.m, opt=solver)
        else:
            opt = SolverFactory("ipopt")
            opt.options["halt_on_ampl_error"] = halt_on_ampl_error
            opt.options["output_file"] = IPOPT_output_file
            results = opt.solve(self.m, tee=verbose, symbolic_solver_labels=True)
            if IPOPT_output_file is not None:
                visualise_IPOPT_output(IPOPT_output_file)

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

