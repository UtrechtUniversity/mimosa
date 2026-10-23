"""Summarise availability using public configuration keys and values."""

from itertools import combinations, product

from mimosa.common.config.parseconfig import get_nested


DAMAGE_MODULE = "model structure.damage module"
DAMAGE_OPTIONS = {
    "ACCREU": (
        "economics.damages.accreu.adaptation",
        "economics.damages.accreu.monetise_mortality",
    ),
    "COACCH": (
        "economics.damages.coacch_slr_withadapt",
        "economics.damages.coacch_combined_slr_nonslr_damages",
    ),
}


def render_availability_examples(available_contexts, context_params):
    """Show the public parameter assignments needed for these contexts."""
    blocks = []
    for requirements in availability_requirements(available_contexts, context_params):
        paths, value_choices = zip(*requirements)
        for values in product(*value_choices):
            assignments = []
            for path, value in zip(paths, values):
                keys = "".join(f"[{key!r}]" for key in path.split("."))
                assignments.append(f"params{keys} = {value!r}")
            highlight_lines = " ".join(
                str(line) for line in range(2, len(assignments) + 2)
            )
            blocks.append("\n".join([
                f'```python hl_lines="{highlight_lines}"',
                "params = load_params()",
                *assignments,
                "model = MIMOSA(params)",
                "```",
            ]))
    return "\n\nor\n\n".join(blocks)


def availability_requirements(available_contexts, context_params):
    """Return alternative sets of configuration requirements.

    Each requirement is (parameter path, allowed values). Prefer the shortest
    combination that selects exactly the documented contexts containing the
    variable. Damage options must include their parent module, so an ACCREU
    option cannot accidentally be presented as applying to other damage modules.
    """
    if set(available_contexts) == set(context_params):
        return ()

    first_params = next(iter(context_params.values()))
    module_paths = [f"model structure.{key}" for key in first_params["model structure"]]
    damage_modules = {
        get_nested(context_params[context], DAMAGE_MODULE.split("."))
        for context in available_contexts
    }
    options = DAMAGE_OPTIONS.get(next(iter(damage_modules)), ()) if len(damage_modules) == 1 else ()
    paths = module_paths + list(options)
    values = {
        context: {path: get_nested(params, path.split(".")) for path in paths}
        for context, params in context_params.items()
    }
    allowed = {
        path: tuple(sorted({values[context][path] for context in available_contexts}, key=str))
        for path in paths
    }

    for count in range(1, len(paths) + 1):
        for selected in combinations(paths, count):
            if any(path in options for path in selected) and DAMAGE_MODULE not in selected:
                continue
            matching = {
                context for context in context_params
                if all(values[context][path] in allowed[path] for path in selected)
            }
            if matching == set(available_contexts):
                return (tuple((path, allowed[path]) for path in selected),)

    # Some patterns need alternatives rather than one conjunction. Keep the
    # actual settings for those cases, never the internal configuration names.
    alternatives = []
    for context in sorted(available_contexts):
        requirements = tuple((path, (values[context][path],)) for path in paths)
        if requirements not in alternatives:
            alternatives.append(requirements)
    return tuple(alternatives)
