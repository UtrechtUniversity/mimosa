---
icon: octicons/gear-24
---

# Variable reference

Each entry lists a model variable's description, units, dimensions and availability.

## Dependency graph

This graph shows the variables and dependencies for the selected model configuration.
Links use the documentation page's configuration, with optional context overrides.
Faint dashed links refer
to the previous time step. Click a node to select it; click empty graph space or
press Escape to clear the selection. Click and drag to pan the zoomed-in graph.
Double-click empty space to fit the graph.
Use **Fit graph** for the overview, or **Focus selected** to read a neighbourhood.
Hover over a node to read its variable reference information.

[Download the graph as SVG](assets/dependency-graphs/coacch.svg){id="dependency-graph-source" download}

<div class="dependency-graph" id="dependency-graph-viewer" data-variable-context="coacch">
  <p class="dependency-graph-configuration"></p>
  <div class="dependency-graph-message" role="status" hidden></div>
  <div class="dependency-graph-controls">
    <label>Variable <select aria-label="Graph variable"></select></label>
    <button type="button" data-action="zoom-out" aria-label="Zoom out">−</button>
    <output class="dependency-graph-zoom" aria-label="Graph zoom"></output>
    <button type="button" data-action="zoom-in" aria-label="Zoom in">+</button>
    <button type="button" data-action="fit">Fit graph</button>
    <button type="button" data-action="focus">Focus selected</button>
  </div>
  <div class="dependency-graph-legend">
    <span class="dependency-control-key">Control variable</span>
    <span class="dependency-calculated-key">Calculated variable</span>
    <span class="dependency-selected-key">Selected variable</span>
    <span class="dependency-incoming-key">Incoming: depends on</span>
    <span class="dependency-outgoing-key">Outgoing: used by</span>
    <span class="dependency-previous-key">Previous time step</span>
  </div>
  <div class="dependency-graph-viewport">
    <p>Loading dependency graph…</p>
  </div>
  <noscript>Enable JavaScript to explore the dependency graph.</noscript>
</div>

## All variables

{variables::reference}
