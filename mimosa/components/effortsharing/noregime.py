"""
Model equations and constraints:
Effort sharing
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint, ModelContext


def get_constraints(
    m: AbstractModel, context: ModelContext
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
