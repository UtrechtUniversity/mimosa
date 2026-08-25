"""
Model equations and constraints:
Damage and adaptation costs, ACCREU specification
"""

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Param,
    Var,
    GeneralConstraint,
    RegionalEquation,
    GlobalEquation,
    value,
    soft_max,
    Any,
    exp,
    quant,
    NonNegativeReals,
    ModelContext,
)


from . import (
    sealevelrise,
    riverine_flooding,
    labour_productivity,
    mortality,
    combined_nslr_adaptation,
)
from .utils import get_adaptation_options


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    ACCREU damage specification

    Currently, the temperature-dependent damages are taken directly from the COACCH
    specification.

    """

    constraints = []

    # In the config, the user can choose whether to use the separate adaptation module for ACCREU or not.
    # This is done using the parameter params["model structure"]["damage module options"]["ACCREU adaptation"] = "separate" or "combined"
    adaptation_options = get_adaptation_options(context)
    adaptation_type = adaptation_options.adaptation_type

    if adaptation_type != "noadaptation":
        m.adaptation_effectiveness_scale_factor = Param(
            doc="::economics.damages.accreu.adaptation_effectiveness_scale_factor"
        )

    # Factor to convert 2017 MER dollars to 2010 PPP dollars:
    m.gdp_ppp_2010_div_gdp_mer_2010 = Param(
        m.regions, doc="regional::economics.gdp_ppp_2010_div_gdp_mer_2010"
    )
    m.dollar_2017_MER_to_2010_PPP = Param(
        m.regions, initialize=lambda m, r: 0.89632 * m.gdp_ppp_2010_div_gdp_mer_2010[r]
    )

    # Get constraints for sea-level rise damages
    constraints.extend(sealevelrise.get_constraints(m, adaptation_options))

    # Get constraints for riverine flooding damages
    constraints.extend(riverine_flooding.get_constraints(m, adaptation_options))

    # Get constraints for labour productivity damages
    constraints.extend(labour_productivity.get_constraints(m, adaptation_options))

    if adaptation_type == "combined":
        # Get constraints for combined adaptation costs, which combines labour productivity and riverine flooding adaptation costs
        # Only if the user has chosen to use the combined adaptation module for ACCREU
        constraints.extend(
            combined_nslr_adaptation.get_constraints(m, adaptation_options)
        )

    # Get constraints for mortality
    monetise_mortality = context.option("damage", "ACCREU_monetise_mortality")
    constraints.extend(
        mortality.get_constraints(m, monetise_mortality=monetise_mortality)
    )

    # Add all non-SLR sectors together

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_costs_abs = Var(m.t, m.regions, units=quant.unit("currency_unit"))
    m.damage_scale_factor = Param(
        doc="::economics.damages.scale factor"
    )  # Not implemented yet
    m.global_damage_costs = Var(
        m.t,
        units=quant.unit("fraction_of_GDP"),
    )
    # Total damages are sum of non-SLR and SLR damages
    constraints.extend(
        [
            RegionalEquation(
                m.damage_costs,
                (
                    (
                        lambda m, t, r: m.combined_labprod_riv_damage_costs[t, r]
                        + m.slr_damage_costs[t, r]
                    )
                    if adaptation_type == "combined"
                    else (
                        lambda m, t, r: m.labourprod_damage_costs_net[t, r]
                        + m.riverine_damage_costs[t, r]
                        + m.slr_damage_costs[t, r]
                    )
                ),
            ),
            RegionalEquation(
                m.damage_costs_abs,
                lambda m, t, r: m.damage_costs[t, r] * m.GDP_gross[t, r],
            ),
            GlobalEquation(
                m.global_damage_costs,
                lambda m, t: (
                    sum(m.damage_costs_abs[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
    )

    if adaptation_type != "noadaptation":
        m.adaptation_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
        m.adaptation_costs_abs = Var(m.t, m.regions, units=quant.unit("currency_unit"))
        m.global_adaptation_costs = Var(
            m.t,
            units=quant.unit("fraction_of_GDP"),
        )
        constraints.extend(
            [
                # Adaptation costs:
                RegionalEquation(
                    m.adaptation_costs,
                    (
                        (
                            lambda m, t, r: m.combined_labprod_riv_adaptation_costs[
                                t, r
                            ]
                            + m.slr_adaptation_costs[t, r]
                        )
                        if adaptation_type == "combined"
                        else (
                            lambda m, t, r: m.labourprod_adaptation_costs[t, r]
                            + m.riverine_adaptation_costs[t, r]
                            + m.slr_adaptation_costs[t, r]
                        )
                    ),
                ),
                RegionalEquation(
                    m.adaptation_costs_abs,
                    lambda m, t, r: m.adaptation_costs[t, r] * m.GDP_gross[t, r],
                ),
                GlobalEquation(
                    m.global_adaptation_costs,
                    lambda m, t: (
                        sum(m.adaptation_costs_abs[t, r] for r in m.regions)
                        / m.global_GDP_gross[t]
                    ),
                ),
            ]
        )
    else:
        m.adaptation_costs = Param(
            m.t, m.regions, units=quant.unit("fraction_of_GDP"), initialize=0.0
        )
        m.adaptation_costs_abs = Param(
            m.t, m.regions, units=quant.unit("currency_unit"), initialize=0.0
        )

    ## Non-market damages:
    if monetise_mortality:
        m.non_market_damage_costs_abs = Var(
            m.t, m.regions, units=quant.unit("currency_unit")
        )
        constraints.append(
            RegionalEquation(
                m.non_market_damage_costs_abs,
                lambda m, t, r: m.mortality_damage_costs_abs[t, r],
            )
        )
    else:
        m.non_market_damage_costs_abs = Param(
            m.t, m.regions, units=quant.unit("currency_unit"), initialize=0.0
        )
    m.market_and_non_market_damage_costs_abs = Var(
        m.t, m.regions, units=quant.unit("currency_unit")
    )
    m.market_and_non_market_damage_costs = Var(
        m.t, m.regions, units=quant.unit("fraction_of_GDP")
    )

    constraints.extend(
        [
            RegionalEquation(
                m.market_and_non_market_damage_costs_abs,
                lambda m, t, r: m.damage_costs_abs[t, r]
                + m.non_market_damage_costs_abs[t, r],
            ),
            RegionalEquation(
                m.market_and_non_market_damage_costs,
                lambda m, t, r: m.market_and_non_market_damage_costs_abs[t, r]
                / m.GDP_gross[t, r],
            ),
        ]
    )

    return constraints
