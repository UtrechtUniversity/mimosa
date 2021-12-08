import numpy as np
import pandas as pd
from model.concrete_model.simulation_mode.utils import read_csv
from model.socialcostofcarbon.scc import SCC
from model.common.config import parseconfig

# pylint: disable=invalid-name

params = parseconfig.params
params["temperature"]["initial"] = "1.16 delta_degC"


def _select_columns(df, year, endyear=np.inf):
    columns = df.columns
    return df[list(columns[(columns >= year) & (columns <= endyear)])]


scc_values = pd.DataFrame()

for damage_q in [0.05, 0.5, 0.95]:
    for rcp in ["cba", "26", "60"]:

        regional_emissions = read_csv(
            f"../Damage functions/Experiments/output/coacch_exp_2.1_CBA_q{damage_q}_SLR_with_adapt_inequal_aversion_zero_*.csv"
            if rcp == "cba"
            else f"../Damage functions/Experiments/output/coacch_exp_scc_SSP2-{rcp}_q{damage_q}_SLR_with_adapt_inequal_aversion_elasmu_*.csv"
        )
        regional_emissions = (
            regional_emissions[regional_emissions["Variable"] == "regional_emissions"]
            .drop(columns="Variable")
            .set_index("Region")
        )

        for pulse_year in [2020, 2030, 2050]:

            outputs = {}

            pulses = [0.001]

            for pulse in [0] + pulses:
                emissions_with_pulse = regional_emissions.copy()
                emissions_with_pulse.loc["USA", str(pulse_year)] += pulse
                params["simulation"]["constraint_variables"] = {
                    "regional_emissions": emissions_with_pulse.to_dict()
                }
                params["economics"]["damages"]["quantile"] = damage_q
                params["economics"]["damages"]["coacch_slr_withadapt"] = True

                model = SCC(params)
                outputs[pulse] = model.output

            # Calculate difference in damages with zero-run

            for pulse in pulses:
                extra_damages = _select_columns(
                    outputs[pulse]["damages_absolute"] - outputs[0]["damages_absolute"],
                    pulse_year,
                    2100,
                ).sum()

                # Discount the values:
                years = extra_damages.index - extra_damages.index[0]

                for prtp in [0.001, 0.015, 0.03]:
                    sdr = 0.021 + prtp
                    discounted_extra_damages = np.exp(-sdr * years) * extra_damages
                    npv_extra_damages = np.trapz(discounted_extra_damages, years)

                    scc = model.quant(
                        f"{npv_extra_damages / pulse} trillion USD2005/GtCO2",
                        "USD2005/(t CO2)",
                    )
                    scenario_str = "CBA" if rcp == "cba" else f"RCP {rcp}"
                    print(
                        f"{pulse_year}, {scenario_str}, pulse {(pulse*1e3)} MtCO2, PRTP {prtp}. SCC: {scc:.1f} USD/tCO2"
                    )
                    scc_values = scc_values.append(
                        {
                            "pulse_year": pulse_year,
                            "scenario_str": scenario_str,
                            "damage_q": damage_q,
                            "pulse": f"{(pulse*1e3)} MtCO2",
                            "SCC": scc,
                            "PRTP": prtp,
                            "SDR": sdr,
                        },
                        ignore_index=True,
                    )

print(scc_values)
scc_values.to_csv("SCC.csv", index=False)
