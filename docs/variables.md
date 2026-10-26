---
icon: octicons/gear-24
---

# Variable reference

Each entry lists a model variable's description, units, dimensions and availability.

## Dependency graph

This graph shows the variables and dependencies in MIMOSA. The graph is interactive: you can zoom, pan, and click on variables to see their details. Use the controls above the graph to select a variable, zoom in/out, fit the graph to the viewport, or focus on a selected variable.

<div class="dependency-graph" id="dependency-graph-viewer" data-variable-context="coacch">
  <div class="dependency-graph-header">
    <div class="dependency-graph-toolbar">
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
    </div>
    <div class="dependency-graph-parameters">
      <p class="dependency-graph-parameters-title">Required parameters</p>
      <div class="dependency-graph-configuration md-typeset"></div>
    </div>
  </div>
  <div class="dependency-graph-message" role="status" hidden></div>
  <div class="dependency-graph-viewport">
    <p>Loading dependency graph…</p>
  </div>
  <noscript>Enable JavaScript to explore the dependency graph.</noscript>
</div>

## All variables

{variables::reference}
