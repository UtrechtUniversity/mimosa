# Documentation development notes

These notes describe the documentation tooling. They live outside `docs/` and are
not included in the published MkDocs site.

Documentation rendering tests require the optional `.[docs]` dependencies. When
these are absent, only the rendering checks are skipped; tests that inspect
metadata or generated Markdown without rendering still run. The normal `.[test]`
installation does not require Markdown or its documentation extensions.

## Parameter reference

Enum options in the parameter reference include a copy button on hover or
keyboard focus. Each button copies the complete `params[...] = value` assignment.
The generated buttons use the theme's `data-clipboard-text` support, sharing
the snippet copy behavior and confirmation without additional JavaScript.

Links to parameter-reference anchors also show the matching parameter card on
hover or keyboard focus. This includes ordinary Markdown links and generated
`param::` links. Clicking still follows the link to the reference page. Cards
reuse the rendered reference HTML, fetched and parsed once on demand, and keep
enum assignment copy buttons. No additional model construction is needed.

Use `[TCRE](#param__temperature.TCRE)` in text and
`\href{./#param__temperature.TCRE}{\text{TCRE}}` in equations. These links work
at any page depth. The browser resolves them to the parameter-reference URL on
hover, keyboard focus or click, preserving native navigation and modified clicks.
Opening a page directly with a `#param__...` fragment redirects to the reference
entry without adding a browser-history entry. Existing links to the parameter
reference still work. Equations need no special build-time URL rewriting.

The `{regionalparams::reference}` marker lists every column from the registered
regional parameter files, grouped by category. It uses a `RegionalParamStore`
with the default documentation configuration, so values use the same IMAGE26
mapping and region order as the model. Each entry contains a compact table with
regions above values; numbers use six significant figures and missing cells show
an em dash. Link to a regional entry with
`[coefficient](#param__regional.ACCREU.riverine_noadapt_ead_linear)` in text or
`\href{./#param__regional.ACCREU.riverine_noadapt_ead_linear}{b_r}` in equations.
Include the category to distinguish identically named columns, and URL-encode
spaces, parentheses and other special characters in column names. These links
reuse the parameter hover cards, including horizontal scrolling through values.
Generated `param::` links also recognise regional source metadata. The store rereads
the CSV files on each documentation rebuild without constructing another model.

## Time- and region-dependent parameter plots

`{timeandregionalparams::reference}` adds population, baseline GDP and baseline
CO₂ emissions to the parameter reference. `docs/scripts/time_regional_parameter_docs.py`
reads their initialized values and units from the shared default documentation
model, keeping its time grid but restricting displayed years to 2025–2100.
Each plot shows all IMAGE regions and identifies the selected scenario and source.

MkDocs publishes the Plotly JSON as virtual files under `assets/parameter-plots/`.
These assets are cached for a build or serve session, so live rebuilds do not
construct another model or repeat data extraction. The existing Plotly plugin
loads them in the browser, and `plotly-resize.js` sizes plots when their collapsed
parameter cards open. No simulation or IPOPT run is needed.

## SLR coefficient tables

The SLR page uses `{{ slr_coefficients("thermal") }}` and equivalent calls for
the initial values, glaciers, Greenland, Antarctica and land-water storage.
`docs/scripts/slr_coefficient_docs.py` supplies symbols, descriptions and units;
values come from `SLR_PROJECTION_PARAMETER_SETS` and the cached documentation
model. The tables compare all three projections and show shared constants
separately. They are generated during the documentation build, including inside
the component docstring, and do not construct additional models.

SLR equation links use `\href{./#slrcoef__slr_gsic_total_ice}{P_{\mathrm{GL}}}`.
They show the matching table header and row on hover or keyboard focus, and
clicking opens the local coefficient table. The fast and slow thermal-expansion
equations link directly to their respective coefficient rows. The cards reuse
the rendered rows on the SLR page.

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
Marker links use `#var__name` to open the dependency graph, independently of the
current page's path. Reference anchors remain available for looking up metadata.

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
Both forms generate graph links such as `#var__damage_costs`. An explicit context is preserved in the link, for example
`#var__coacch::damage_costs`. Otherwise, the graph uses the page context,
defaulting to `coacch` when none is supplied.

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

Plotly charts in content tabs are resized when a tab opens by
`docs/assets/plotly-resize.js`. It calls `Plotly.relayout` with `autosize: true`
synchronously after the tab becomes visible, before the next paint. This avoids
the 100 ms delay in `Plotly.Plots.resize` and the resulting first-opening jump.
Only initialized, visible plots are updated, including those inside nested tabs.
Keep this script in `extra_javascript` when changing the plotting plugin or theme.

Dependency graphs are generated automatically for every entry in
`DOCUMENTATION_CONFIGS` when running `mkdocs build` or `mkdocs serve` in the
`accreu` environment. Install Graphviz and PyGraphviz first with
`conda install -c conda-forge graphviz pygraphviz`; the Python documentation
extras include PyGraphviz, but its Graphviz system libraries must be available.
No separate exporter command is needed.

The graphs reuse the concrete models and equations already cached for variable
references. SVG layouts and their configuration index are cached once per command
or serve session, including after a failed rebuild. MkDocs writes these as virtual
assets directly into the site, without creating files in the watched `docs/`
directory. Restart `mkdocs serve` after changing model equations, variable
metadata or documentation configurations. The configuration above each graph
shows the parameter assignments needed to reproduce it, omitting defaults.

The exporter uses the simulator's dependency analysis and retains isolated public
variables and cyclic dependencies. Control and calculated variables have distinct
colours. Previous-time links are faint dashed edges and do not constrain layout.
Avoided-damage equations are attached symbolically; no baseline, simulation,
prerun or solve is performed. The browser viewer is in
`docs/assets/dependency-graph.js` and caches downloaded assets per page.
The selected context controls both the graph and its variable information.
Node selection uses `history.replaceState` so deep links remain shareable without
adding a browser-history entry for every click. Background clicks and Escape
clear the selection and remove the variable from the URL.
Double-clicking the graph background also restores the fit view.
Mouse dragging pans the graph without changing its zoom or selection. Movements
under four pixels still count as clicks; touch scrolling remains native.
Use `[damage_costs](#var__damage_costs)` on any documentation page to open the
graph in a native dialog. Use `[damage_costs](#var__coacch::damage_costs)` to
override the page context. No path or CSS class is needed. The viewer resolves
the variable reference page relative to its own script and reuses its markup.
In equations, use `\href{./#var__temperature}{T_t}`. The `./` avoids the macros
plugin interpreting `{#` as a template comment. Clicks are handled on the page
container, including links created later by MathJax.
Hovering a variable link for 250 ms, or focusing it with the keyboard, shows the
same information card as a graph node. Text, tables and equations use the page's
context unless the link explicitly overrides it. The reference HTML is fetched
and parsed once on demand, shared with the modal; hovering does not fetch graph
SVGs or their index. Cards remain open when moving into them, and close on Escape,
clicking outside, page scrolling or window resizing. Pending hover requests are cancelled
when the pointer leaves, and listeners are removed on page navigation.
Modal selections leave the page URL and
browser history unchanged. Escape clears a selected variable; when none is
selected, Escape closes the dialog. The close button always closes it. Variable
links open with the requested node selected. Its information card appears on
node hover or keyboard focus.
Unavailable variables offer configurations that contain them.
Node hover cards clone the matching variable-reference admonition, using the
graph panel's `data-variable-context` to choose the metadata variant. They reuse
the reference page already loaded for the modal, including availability examples.

Activate the `accreu` Conda environment, then run:

```sh
python -m pytest tests/unittests/test_variable_docs.py tests/unittests/test_variable_references.py tests/unittests/test_variable_rendering.py tests/unittests/test_variable_availability.py
python -m mkdocs build --strict
```

The tests check metadata collection, configuration coverage, branch-specific
variables and model reuse. They prevent simulation and solve methods from being
called while constructing the documentation models.
