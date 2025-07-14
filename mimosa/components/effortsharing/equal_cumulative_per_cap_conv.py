"""
Model equations and constraints:
Effort sharing
"""

import os
import pandas as pd
import numpy as np

from typing import Sequence
from mimosa.common import (
    AbstractModel,
    Var,
    Param,
    GeneralConstraint,
    Constraint,
    RegionalConstraint,
    RegionalInitConstraint,
    RegionalEquation,
    GlobalEquation,
    RegionalSoftEqualityConstraint,
    Any,
    quant,
    value,
    soft_min,
)

from .equal_cumulative_per_cap import _initialize_ecpc_debt


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "equal_cumulative_per_capita_conv"
    model = MIMOSA(params)
    ```
    """

    _initialize_ecpc_debt(m)

    m.percapconv_share_pop = Param(
        m.t,
        m.regions,
        initialize=lambda m, t, r: m.population[t, r] / m.global_population[t],
    )

    return [
        RegionalSoftEqualityConstraint(
            lambda m, t, r: m.percapconv_share_pop[t, r] * m.global_emissions[t],
            lambda m, t, r: m.regional_emission_allowances[t, r],
            epsilon=None,
            absolute_epsilon=0.001,
            ignore_if=lambda m, t, r: t == 0,
            name="percapconv_rule",
        ),
    ]
