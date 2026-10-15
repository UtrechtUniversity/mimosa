"""Shared model and variable metadata for the documentation build.

Only the default configuration is collected for now. Selectable configurations,
reference resolution and rendering can be added without changing model variables.
"""

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Tuple

from mimosa import MIMOSA
from mimosa.common import ConcreteModel, Var
from mimosa.common.config.parseconfig import check_params
from mimosa.common.pyomo_utils import get_indices, get_unit


@dataclass(frozen=True)
class VariableMetadata:
    """Declaration metadata, with no model references or variable values."""

    name: str
    description: Optional[str]
    unit: str
    dimensions: Tuple[str, ...]
    context: str
    has_declared_units: bool


def collect_variables(model: ConcreteModel, context: str) -> Tuple[VariableMetadata, ...]:
    """Snapshot public Var declarations without reading their values.

    Missing descriptions and units are preserved for later validation. In
    particular, Pyomo can report dimensionless units even when none were declared.
    Parameters and export-derived output series are not model variables.
    """
    return tuple(
        VariableMetadata(
            name=var.name,
            description=var.doc,
            unit=get_unit(var),
            dimensions=tuple(get_indices(var)) if var.is_indexed() else (),
            context=context,
            has_declared_units=var.get_units() is not None,
        )
        for var in sorted(model.component_objects(Var), key=lambda var: var.name)
        if not var.name.startswith("_")
    )


@dataclass(frozen=True)
class DocumentationContext:
    """The model shared by parameter, constraint and variable documentation."""

    model: ConcreteModel
    parser_tree: dict
    variables: Tuple[VariableMetadata, ...]


@lru_cache(maxsize=1)
def get_documentation_context() -> DocumentationContext:
    """Construct the default documentation model once, without a prerun.

    Both MkDocs entry points import this provider through docs.scripts so they
    share the cache. Variables added only after a baseline run are outside this
    initial catalogue; no baseline simulation or solve is performed here.
    """
    params, parser_tree = check_params({}, return_parser_tree=True)
    model = MIMOSA(params, prerun=False).concrete_model
    return DocumentationContext(
        model=model,
        parser_tree=parser_tree,
        variables=collect_variables(model, context="default"),
    )
