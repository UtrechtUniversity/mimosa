"""
Model equations and constraints:
Effort sharing
"""

from typing import Sequence
from mimosa.common import AbstractModel, GeneralConstraint


def get_constraints(m: AbstractModel) -> Sequence[GeneralConstraint]:
    """
    Usage:
    ```python hl_lines="2"
    params = load_params()
    params["effort sharing"]["regime"] = "noregime"
    model = MIMOSA(params)
    ```

    By default, no effort-sharing regime is imposed.

    """

    return []
