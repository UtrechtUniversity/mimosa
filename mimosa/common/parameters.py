"""Parameter construction with optional input-source metadata."""

from dataclasses import dataclass
from typing import Any

from pyomo.environ import Param as PyomoParam


@dataclass(frozen=True)
class SourcedValue:
    """Resolved initialization values and their documentation source key.

    Source keys use MIMOSA's existing ``::config.path``,
    ``regional::category.name`` or ``timeandregional::variable`` conventions.
    Values are passed to Pyomo unchanged; this object does not load or convert data.
    """

    values: Any
    documentation_key: str


def Param(*args, **kwargs) -> PyomoParam:
    """Create a native Pyomo parameter, unwrapping sourced initialization data.

    Ordinary Pyomo arguments are forwarded unchanged. A :class:`SourcedValue`
    initializer supplies both ``initialize`` and ``doc``, so an explicit ``doc``
    cannot be combined with it. Use ``PyomoParam`` for component filters and type
    checks; this function is a factory, not a component class.
    """
    initializer = kwargs.get("initialize")
    if isinstance(initializer, SourcedValue):
        if "doc" in kwargs:
            raise ValueError(
                "doc is generated automatically for SourcedValue initialization; "
                "omit the explicit doc argument."
            )
        kwargs["initialize"] = initializer.values
        kwargs["doc"] = initializer.documentation_key

    return PyomoParam(*args, **kwargs)
