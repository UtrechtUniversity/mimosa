"""Shared model and variable metadata for the documentation build.

Named configurations cover selectable modules and variable-declaring options.
They are documentation examples, not an exhaustive combination of all settings.
"""

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Tuple

from mimosa import MIMOSA
from mimosa.common import ConcreteModel, Var
from mimosa.common.config.parseconfig import check_params
from mimosa.common.pyomo_utils import get_indices, get_unit
from mimosa.components.after_initialisation import avoided_damages


def _damage_config(module, **options):
    return {
        "model structure": {"damage module": module},
        "economics": {"damages": options},
    }


def _effortsharing_config(module):
    # Use the trading and welfare choices recommended by the component docs.
    return {
        "model structure": {
            "effortsharing module": module,
            "emissiontrade module": "emissiontrade",
            "welfare module": "cost_minimising",
        },
        "economics": {"MAC": {"rel_mitigation_costs_min_level": -0.5}},
    }


# Every entry is a set of overrides on the ordinary model defaults. Keep these
# explicit so new variable-declaring branches are easy to add and review.
DOCUMENTATION_CONFIGS = {
    "coacch": _damage_config(
        "COACCH", coacch_slr_withadapt=True, coacch_combined_slr_nonslr_damages=False
    ),
    "accreu_noadaptation": _damage_config(
        "ACCREU", accreu={"adaptation": "noadaptation", "monetise_mortality": True}
    ),
    "accreu_sectoral": _damage_config(
        "ACCREU", accreu={"adaptation": "sectoral", "monetise_mortality": True}
    ),
    "accreu_sectoral_no_mortality_monetisation": _damage_config(
        "ACCREU", accreu={"adaptation": "sectoral", "monetise_mortality": False}
    ),
    "emissiontrade": {"model structure": {"emissiontrade module": "emissiontrade"}},
    "effortsharing_equal_mitigation_costs": _effortsharing_config(
        "equal_mitigation_costs"
    ),
    "effortsharing_equal_total_costs": _effortsharing_config("equal_total_costs"),
    "effortsharing_per_cap_convergence": _effortsharing_config("per_cap_convergence"),
    "effortsharing_ability_to_pay": _effortsharing_config("ability_to_pay"),
    "effortsharing_equal_cumulative_per_cap": _effortsharing_config(
        "equal_cumulative_per_cap"
    ),
    "welfare_cost_minimising": {
        "model structure": {"welfare module": "cost_minimising"}
    },
    "welfare_inequal_aversion_general": {
        "model structure": {"welfare module": "inequal_aversion_general"}
    },
    "objective_globalcosts": {"model structure": {"objective module": "globalcosts"}},
}


@dataclass(frozen=True)
class VariableMetadata:
    """Declaration metadata, with no model references or variable values."""

    name: str
    description: Optional[str]
    unit: str
    dimensions: Tuple[str, ...]
    context: str
    has_declared_units: bool
    requires_baseline: bool = False


def collect_variables(
    model: ConcreteModel, context: str, baseline_variables: Tuple[str, ...] = ()
) -> Tuple[VariableMetadata, ...]:
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
            requires_baseline=var.name in baseline_variables,
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
    params: dict


@lru_cache(maxsize=None)
def get_documentation_context(context: str = "default") -> DocumentationContext:
    """Construct each named documentation model once, without a prerun.

    Both MkDocs entry points import this provider through docs.scripts so they
    share the cache. The former default context is an alias for coacch.
    Baseline-dependent declarations are added without attaching or evaluating
    their equations; no baseline simulation or solve is performed here.
    """
    if context == "default":
        return get_documentation_context("coacch")
    if context not in DOCUMENTATION_CONFIGS:
        raise ValueError(f"Unknown documentation context: {context!r}")
    params, parser_tree = check_params(
        deepcopy(DOCUMENTATION_CONFIGS[context]), return_parser_tree=True
    )
    model = MIMOSA(params, prerun=False).concrete_model
    baseline_variables = tuple(
        equation.lhs for equation in avoided_damages.get_constraints(model)
    )
    return DocumentationContext(
        model=model,
        parser_tree=parser_tree,
        variables=collect_variables(model, context, baseline_variables),
        params=params,
    )


@lru_cache(maxsize=1)
def get_variable_catalogue() -> Tuple[VariableMetadata, ...]:
    """Collect the configured contexts, preserving entries with the same name."""
    return tuple(
        variable
        for context in DOCUMENTATION_CONFIGS
        for variable in get_documentation_context(context).variables
    )


def clear_documentation_cache():
    """Release all contexts and their combined metadata between builds."""
    get_variable_catalogue.cache_clear()
    get_documentation_context.cache_clear()
