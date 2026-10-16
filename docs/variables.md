---
icon: octicons/gear-24
---

# Variable reference

Each entry lists a model variable's description, units, dimensions and availability.

## Dependency graph demo

This graph shows the actual variables and dependencies for **ACCREU with sectoral
adaptation and solver-controlled adaptation spending**. Faint dashed links refer
to the previous time step. Click a node to select it; click empty graph space or
press Escape to clear the selection. Double-click empty space to fit the graph.
Use **Fit graph** for the overview, or **Focus selected** to read a neighbourhood.

[Download the graph as SVG](assets/dependency-demo.svg){id="dependency-demo-source" download}

<div class="dependency-demo" id="dependency-demo">
  <div class="dependency-demo-controls">
    <label>Variable <select aria-label="Graph variable"></select></label>
    <button type="button" data-action="zoom-out" aria-label="Zoom out">−</button>
    <output class="dependency-demo-zoom" aria-label="Graph zoom"></output>
    <button type="button" data-action="zoom-in" aria-label="Zoom in">+</button>
    <button type="button" data-action="fit">Fit graph</button>
    <button type="button" data-action="focus">Focus selected</button>
  </div>
  <div class="dependency-demo-legend">
    <span class="demo-control-key">Control variable</span>
    <span class="demo-calculated-key">Calculated variable</span>
    <span class="demo-selected-key">Selected variable</span>
    <span class="demo-incoming-key">Incoming: depends on</span>
    <span class="demo-outgoing-key">Outgoing: used by</span>
    <span class="demo-previous-key">Previous time step</span>
  </div>
  <div class="dependency-demo-viewport">
    <p>Loading dependency graph…</p>
  </div>
  <noscript>Enable JavaScript to explore the dependency graph demo.</noscript>
</div>

## All variables

{variables::reference}
