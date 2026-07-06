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


def get_constraints(
    m: AbstractModel, context: ModelContext
) -> Sequence[GeneralConstraint]:
    """
    ACCREU damage specification

    Currently, the temperature-dependent damages are taken directly from the COACCH
    specification.

    """

    # In the config, the user can choose whether to use the separate adaptation module for ACCREU or not.
    # This is done using the parameter params["model"]["damage module options"]["ACCREU adaptation"] = "separate" or "combined"
    combined_adaptation = context.option("damage", "ACCREU adaptation") == "combined"

    constraints = []

    # Get constraints for sea-level rise damages
    constraints.extend(sealevelrise.get_constraints(m))

    # Get constraints for riverine flooding damages
    constraints.extend(
        riverine_flooding.get_constraints(
            m, with_combined_adaptation=combined_adaptation
        )
    )

    # Get constraints for labour productivity damages
    constraints.extend(
        labour_productivity.get_constraints(
            m, with_combined_adaptation=combined_adaptation
        )
    )

    if combined_adaptation:
        # Get constraints for combined adaptation costs, which combines labour productivity and riverine flooding adaptation costs
        # Only if the user has chosen to use the combined adaptation module for ACCREU
        constraints.extend(combined_nslr_adaptation.get_constraints(m))

    # Get constraints for mortality
    monetise_mortality = context.option("damage", "ACCREU_monetise_mortality")
    constraints.extend(
        mortality.get_constraints(m, monetise_mortality=monetise_mortality)
    )

    # Add all non-SLR sectors together

    m.damage_costs = Var(m.t, m.regions, units=quant.unit("fraction_of_GDP"))
    m.damage_costs_abs = Var(m.t, m.regions, units=quant.unit("currency_unit"))
    m.damage_scale_factor = Param(doc="::economics.damages.scale factor")
    m.damage_relative_global = Var(
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
                    if combined_adaptation
                    else (
                        lambda m, t, r: m.labourprod_damage_costs[t, r]
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
                m.damage_relative_global,
                lambda m, t: (
                    sum(m.damage_costs_abs[t, r] for r in m.regions)
                    / m.global_GDP_gross[t]
                ),
            ),
        ]
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
