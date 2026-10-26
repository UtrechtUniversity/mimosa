"""Resolve variable markers and prepare links for the documentation renderer."""

import posixpath
from dataclasses import dataclass, replace
from typing import Optional, Tuple
from urllib.parse import quote

from docs.scripts.variable_docs import VariableMetadata, get_variable_catalogue


def variable_anchor(name: str, context: str) -> str:
    """Keep links stable when descriptions change or entries are regrouped."""
    return f"variable-{context}--{name}"


@dataclass(frozen=True)
class VariableEntry:
    """One metadata variant and all contexts sharing that variant."""

    metadata: VariableMetadata
    contexts: Tuple[str, ...]

    @property
    def anchors(self) -> Tuple[str, ...]:
        # A merged reference entry must retain the anchor for each context.
        return tuple(
            variable_anchor(self.metadata.name, context) for context in self.contexts
        )


def group_variables(catalogue: Tuple[VariableMetadata, ...]) -> Tuple[VariableEntry, ...]:
    """Merge identical metadata while preserving differing variants and contexts."""
    groups = {}
    for variable in sorted(catalogue, key=lambda variable: (variable.name, variable.context)):
        signature = (
            variable.name,
            variable.description,
            variable.unit,
            variable.dimensions,
            variable.has_declared_units,
            variable.requires_baseline,
        )
        groups.setdefault(signature, []).append(variable)

    return tuple(
        VariableEntry(
            metadata=variables[0],
            contexts=tuple(sorted({variable.context for variable in variables})),
        )
        for variables in groups.values()
    )


def resolve_variable_reference(
    marker: str,
    page_context: Optional[str] = None,
    page_path: Optional[str] = None,
    catalogue: Optional[Tuple[VariableMetadata, ...]] = None,
) -> VariableMetadata:
    """Resolve var::name or varref::context::name to declaration metadata.

    The renderer supplies variable_context from page frontmatter and the page's
    source path. An explicit marker context overrides the page context. Without
    a context, all declarations of the name must have identical metadata.
    """
    location = f"{page_path}: " if page_path else ""
    parts = marker.split("::")
    if len(parts) not in (2, 3) or parts[0] not in ("var", "varref") or not all(parts):
        raise ValueError(
            f"{location}Invalid variable reference {marker!r}; "
            "use var::name, varref::name, or add a context before the name"
        )

    name = parts[-1]
    context = parts[1] if len(parts) == 3 else page_context
    if context == "default":
        context = "coacch"
    if catalogue is None:
        catalogue = get_variable_catalogue()
    contexts = {variable.context for variable in catalogue}
    if context is not None and (not isinstance(context, str) or context not in contexts):
        raise ValueError(f"{location}Unknown variable context {context!r} in {marker!r}")

    entries = [entry for entry in group_variables(catalogue) if entry.metadata.name == name]
    if not entries:
        raise ValueError(f"{location}Unknown variable {name!r} in {marker!r}")
    available = ", ".join(
        sorted({context for entry in entries for context in entry.contexts})
    )
    if context is not None:
        for entry in entries:
            if context in entry.contexts:
                return replace(entry.metadata, context=context)
        raise ValueError(
            f"{location}Variable {name!r} is unavailable in context {context!r}; "
            f"available contexts: {available}"
        )
    if len(entries) > 1:
        raise ValueError(
            f"{location}Ambiguous variable {name!r}; available contexts: {available}. "
            f"Set variable_context or use {parts[0]}::<context>::{name}"
        )
    return entries[0].metadata


def variable_reference_url(
    variable: VariableMetadata, current_page_url: str, reference_page_url: str
) -> str:
    """Link between MkDocs page URLs, with or without directory URLs enabled."""
    anchor = quote(variable_anchor(variable.name, variable.context), safe="-_.")
    if current_page_url == reference_page_url:
        return f"#{anchor}"
    directory = (
        current_page_url if current_page_url.endswith("/") else posixpath.dirname(current_page_url)
    )
    relative_url = posixpath.relpath(reference_page_url, start=directory or ".")
    if reference_page_url.endswith("/"):
        relative_url += "/"
    return f"{relative_url}#{anchor}"
