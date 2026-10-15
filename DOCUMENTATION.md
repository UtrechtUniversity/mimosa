# Documentation development notes

These notes describe the documentation tooling. They live outside `docs/` and are
not included in the published MkDocs site.

## Variable catalogue

[`docs/scripts/variable_docs.py`](docs/scripts/variable_docs.py) collects variable
names, descriptions, units and dimensions from constructed Pyomo models.

`DOCUMENTATION_CONFIGS` contains named sets of ordinary configuration overrides;
the remaining settings use MIMOSA's defaults. The configurations cover COACCH's
damage options, ACCREU's adaptation modes and mortality monetisation, and the
other selectable modules. `globalcostpool` is intentionally omitted because it
is planned for removal.

When adding a module or an option that declares different variables, add a
representative configuration to this dictionary. Also add a context when an
existing variable name has a different meaning. Settings that only change
coefficients or equations usually do not need additional contexts.

The documentation scripts share each model and its metadata for the duration of
a build. Models are constructed with `prerun=False`; no simulations or solves
are performed. Avoided-damage variables are declared separately and marked as
requiring a baseline, without attaching or evaluating their equations. Parameters
and series created only during export are excluded from the catalogue.

## Variable reference resolution

[`docs/scripts/variable_references.py`](docs/scripts/variable_references.py) resolves
`var::name` and `varref::name`. Both accept an explicit context, for example
`var::accreu_combined::combined_labprod_riv_damage_costs`.

The resolver accepts the page's `variable_context` frontmatter value as its default
context. An explicit context in a marker overrides it. With no context, a name is
accepted only when it has one metadata variant across the catalogue. Unknown
variables, unknown contexts, unavailable variables and ambiguous names raise
errors that include the source page when supplied.

Entries are merged only when their name, description, units, dimensions, declared
unit status and baseline requirement match. A merged entry retains all of its
contexts and their anchors, such as `variable-accreu_sectoral--damage_costs`.
Editing descriptions or regrouping entries therefore preserves existing links.
The URL helper calculates links from the current page's output URL, supporting
both directory URLs and `.html` pages.

This step provides resolution and link helpers. Connecting them to page
frontmatter and rendering markers into pages and component docstrings is the
next step; authoring markers in public pages is not enabled yet.

## Validation

Activate the `accreu` Conda environment, then run:

```sh
python -m pytest tests/unittests/test_variable_docs.py tests/unittests/test_variable_references.py
python -m mkdocs build --strict
```

The tests check metadata collection, configuration coverage, branch-specific
variables and model reuse. They prevent simulation and solve methods from being
called while constructing the documentation models.
