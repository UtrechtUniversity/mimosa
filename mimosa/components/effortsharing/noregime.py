"""
Model equations and constraints:
Effort sharing
"""

from typing import Sequence
from mimosa.common import ConcreteModel, GeneralConstraint

from mimosa.core.model_inputs import ModelInputs


def get_constraints(
    m: ConcreteModel, inputs: ModelInputs
) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["model structure"]["effortsharing module"] = "noregime"
    model = MIMOSA(params)
    ```

    By default, no effort-sharing regime is imposed.

    """

    return []
