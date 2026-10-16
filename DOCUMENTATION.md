# Documentation development notes

These notes describe the documentation tooling. They live outside `docs/` and are
not included in the published MkDocs site.

## Variable catalogue

[`docs/scripts/variable_docs.py`](docs/scripts/variable_docs.py) collects variable
names, descriptions, units and dimensions from constructed Pyomo models.

`DOCUMENTATION_CONFIGS` contains named sets of ordinary configuration overrides;
the remaining settings use MIMOSA's defaults. Choose configurations to cover
distinct variable declarations, rather than every selectable module. `nodamage`
and `ACCREU_CGE` need no separate context because their variable names are already
covered by the other damage modules. `globalcostpool` is intentionally omitted
because it is planned for removal. These omissions are allowed by the module
coverage test; other modules that introduce variables still require coverage.

`globaldamagepool` is also currently omitted by choice. Its `financial_transfer`
and `financial_transfer_abs` variables are therefore absent from the catalogue,
and the financial-transfer module coverage test reports this gap.

When adding a module or an option that declares different variables, add a
representative configuration to this dictionary. Also add a context when an
existing variable name has a different meaning. Settings that only change
coefficients or equations usually do not need additional contexts.

The documentation scripts share each model and its metadata for the duration of
the command. During `mkdocs serve`, successful rebuilds and rebuild errors reuse
the cached models. Restart `mkdocs serve` after changing variable `doc=...`
descriptions, declarations, units, or the documentation configurations. Markdown
and component-docstring edits can use the normal live rebuilds.

Models are constructed with `prerun=False`; no simulations or solves
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

## Rendering variable documentation

[`docs/scripts/variable_rendering.py`](docs/scripts/variable_rendering.py) expands
markers through the existing MkDocs hooks. Add descriptions directly to ordinary
`Var(..., doc="...")` declarations. Descriptions are escaped plain text; Markdown
and HTML inside them are not interpreted.

Set a page's default context in its existing YAML frontmatter:

```yaml
---
variable_context: accreu_sectoral
---
```

Use `var::damage_costs` for a linked name, description, units and dimensions, or
`varref::damage_costs` for just the linked name. An explicit context such as
`var::coacch::damage_costs` overrides the page default. These markers also work in
component docstrings rendered on that page. Markers in inline code, code blocks,
existing links, HTML attributes, comments, scripts and styles remain literal.

The standalone `{variables::reference}` marker generates the complete reference
in `docs/variables.md` as flat `variable` admonitions, matching the
parameter reference style. Conditional variables show configuration code blocks
under "Available when:", with "or" between the alternatives.
Missing descriptions and units are shown explicitly for
now; completeness checks can be introduced once declarations have been documented.
The reference is expanded before Markdown conversion. Individual variable
markers are expanded after mkdocstrings rendering, so pages and docstrings use
the same context and error handling.

The reference shows availability only for variable names absent from at least one
documented configuration. It shows public configuration requirements as assignments
to `params`, rather than internal context names. Variables present everywhere omit
availability details, even when their descriptions differ between configurations.
All anchors are retained.

`variable_availability.py` finds the shortest combination of module choices and
relevant damage options that distinguishes contexts containing a variable from
those without it. Damage options are always paired with their parent module.
This summarises the documented configurations; maintaining representative branch
coverage remains important. Unrelated choices, such as mortality monetisation
for a variable present with either setting, are omitted.

## Validation

The dependency graph prototype uses one exported ACCREU sectoral configuration.
Regenerate `docs/assets/dependency-demo.svg` with
`python -m docs.scripts.generate_dependency_demo` in the `accreu` environment.
It uses the simulator's dependency graph, omits previous-time links, and retains
isolated public variables. Avoided-damage equations are attached symbolically;
no baseline, simulation, prerun or solve is performed. The SVG is a snapshot and
is not regenerated by MkDocs builds. The browser viewer is in
`docs/assets/dependency-demo.js`; no context switching is implemented yet.

Activate the `accreu` Conda environment, then run:

```sh
python -m pytest tests/unittests/test_variable_docs.py tests/unittests/test_variable_references.py tests/unittests/test_variable_rendering.py tests/unittests/test_variable_availability.py
python -m mkdocs build --strict
```

The tests check metadata collection, configuration coverage, branch-specific
variables and model reuse. They prevent simulation and solve methods from being
called while constructing the documentation models.
