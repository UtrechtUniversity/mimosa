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


def Param(*args, source_key=None, **kwargs) -> PyomoParam:
    """Create a native Pyomo parameter, unwrapping sourced initialization data.

    Ordinary Pyomo arguments are forwarded unchanged. A :class:`SourcedValue`
    initializer supplies values and ``source_key`` metadata, leaving ``doc`` free
    for a description. An explicit ``source_key`` can also label ordinary values.
    Use ``PyomoParam`` for component filters and type checks; this function is a
    factory, not a component class.
    """
    initializer = kwargs.get("initialize")
    if isinstance(initializer, SourcedValue):
        if source_key is not None and source_key != initializer.documentation_key:
            raise ValueError("source_key conflicts with the sourced initializer.")
        kwargs["initialize"] = initializer.values
        source_key = initializer.documentation_key

    parameter = PyomoParam(*args, **kwargs)
    parameter.source_key = source_key
    return parameter
