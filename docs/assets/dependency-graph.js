// Resolve the reference page from this asset, independently of the current page.
const dependencyGraphPage = new URL("../variables/", document.currentScript.src);

async function initializeDependencyGraph(panel, source, dialog = null) {
    const viewport = panel.querySelector(".dependency-graph-viewport");
    const select = panel.querySelector("select");
    const focusButton = panel.querySelector('[data-action="focus"]');

    try {
        const response = await fetch(source);
        if (!response.ok) throw new Error(`Graph request failed: ${response.status}`);
        const graphDocument = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
        const svg = graphDocument.documentElement;
        svg.setAttribute("role", "group");
        svg.setAttribute("aria-label", "ACCREU sectoral variable dependencies");
        viewport.replaceChildren(svg);

        const nodes = Array.from(svg.querySelectorAll("g.node"));
        const edges = Array.from(svg.querySelectorAll("g.edge"));
        const { width, height } = svg.viewBox.baseVal;
        const focusZoom = 0.85;
        let scale = 1;
        let selected = null;

        nodes.forEach(node => {
            const name = node.querySelector("title").textContent;
            node.dataset.variable = name;
            node.classList.add("dependency-node");
            const link = node.querySelector("a");
            link.setAttribute("href", `?graph_variable=${encodeURIComponent(name)}#dependency-graph`);
            link.setAttribute("aria-label", `Highlight ${name}`);
            link.addEventListener("click", event => {
                event.preventDefault();
                choose(name);
                if (scale < focusZoom) focusSelected();
            });
        });
        select.add(new Option("No selection", ""));
        nodes.map(node => node.dataset.variable).sort().forEach(name => {
            select.add(new Option(name, name));
        });
        edges.forEach(edge => {
            const [source, target] = edge.querySelector("title").textContent.split("->");
            edge.dataset.source = source;
            edge.dataset.target = target;
        });

        function highlight(name) {
            selected = name;
            select.value = name || "";
            focusButton.disabled = !name;
            const incoming = edges.filter(edge => edge.dataset.target === name).map(edge => edge.dataset.source);
            const outgoing = edges.filter(edge => edge.dataset.source === name).map(edge => edge.dataset.target);
            nodes.forEach(node => {
                const id = node.dataset.variable;
                node.classList.toggle("is-selected", id === name);
                node.classList.toggle("is-incoming", id !== name && incoming.includes(id));
                node.classList.toggle("is-outgoing", id !== name && outgoing.includes(id));
                node.classList.toggle("is-muted", !!name && id !== name && !incoming.includes(id) && !outgoing.includes(id));
                node.querySelector("a").setAttribute("aria-current", id === name ? "true" : "false");
            });
            edges.forEach(edge => {
                const kind = edge.dataset.target === name ? "incoming" : edge.dataset.source === name ? "outgoing" : "normal";
                edge.classList.add("dependency-edge");
                edge.classList.toggle("incoming", kind === "incoming");
                edge.classList.toggle("outgoing", kind === "outgoing");
                edge.classList.toggle("normal", kind === "normal");
                edge.classList.toggle("is-muted", !!name && kind === "normal");
            });
        }

        function choose(name) {
            if (!dialog) {
                const url = new URL(location.href);
                if (name) url.searchParams.set("graph_variable", name);
                else url.searchParams.delete("graph_variable");
                url.hash = "dependency-graph";
                history.replaceState(history.state, "", url);
            }
            highlight(name);
            if (!name && document.activeElement?.closest(".dependency-node")) {
                document.activeElement.blur();
            }
        }

        function setZoom(next) {
            const centerX = (viewport.scrollLeft + viewport.clientWidth / 2) / scale;
            const centerY = (viewport.scrollTop + viewport.clientHeight / 2) / scale;
            scale = Math.max(0.05, Math.min(3, next));
            svg.style.width = `${width * scale}px`;
            svg.style.height = `${height * scale}px`;
            viewport.scrollLeft = centerX * scale - viewport.clientWidth / 2;
            viewport.scrollTop = centerY * scale - viewport.clientHeight / 2;
            panel.querySelector("output").textContent = `${Math.round(scale * 100)}%`;
        }

        function fitGraph() {
            panel.classList.add("is-overview");
            setZoom(Math.min(viewport.clientWidth / width, viewport.clientHeight / height));
            viewport.scrollTo(0, 0);
        }

        function focusSelected() {
            if (!selected) return;
            panel.classList.remove("is-overview");
            setZoom(Math.max(scale, focusZoom));
            const node = nodes.find(node => node.dataset.variable === selected).getBoundingClientRect();
            const frame = viewport.getBoundingClientRect();
            viewport.scrollLeft += node.left - frame.left + node.width / 2 - viewport.clientWidth / 2;
            viewport.scrollTop += node.top - frame.top + node.height / 2 - viewport.clientHeight / 2;
        }

        function focusVariable(requested) {
            const exists = nodes.some(node => node.dataset.variable === requested);
            highlight(exists ? requested : null);
            if (exists) focusSelected();
        }

        select.addEventListener("change", () => {
            choose(select.value || null);
            focusSelected();
        });

        let pan = null;
        let dragged = false;
        viewport.addEventListener("pointerdown", event => {
            if (event.button !== 0 || event.pointerType === "touch" || !event.target.closest("svg")) return;
            dragged = false;
            pan = {
                pointerId: event.pointerId,
                x: event.clientX, y: event.clientY,
                left: viewport.scrollLeft, top: viewport.scrollTop,
            };
        });
        viewport.addEventListener("pointermove", event => {
            if (!pan || event.pointerId !== pan.pointerId) return;
            const dx = event.clientX - pan.x;
            const dy = event.clientY - pan.y;
            // Allow a small movement on an ordinary node click.
            if (!dragged && Math.hypot(dx, dy) < 4) return;
            if (!dragged) viewport.setPointerCapture(event.pointerId);
            dragged = true;
            viewport.classList.add("is-panning");
            viewport.scrollLeft = pan.left - dx;
            viewport.scrollTop = pan.top - dy;
            event.preventDefault();
        });
        function endPan() {
            pan = null;
            viewport.classList.remove("is-panning");
        }
        viewport.addEventListener("pointerup", endPan);
        viewport.addEventListener("pointercancel", endPan);
        viewport.addEventListener("lostpointercapture", endPan);
        viewport.addEventListener("dragstart", event => event.preventDefault());
        // Releasing a drag must not select a node or clear the selection.
        viewport.addEventListener("click", event => {
            if (dragged && event.detail !== 0) {
                event.preventDefault();
                event.stopImmediatePropagation();
                dragged = false;
            }
        }, true);
        viewport.addEventListener("click", event => {
            if (!event.target.closest(".dependency-node")) choose(null);
        });
        viewport.addEventListener("dblclick", event => {
            if (!event.target.closest(".dependency-node")) {
                choose(null);
                fitGraph();
            }
        });
        if (dialog) {
            dialog.addEventListener("cancel", event => {
                if (selected) {
                    event.preventDefault();
                    choose(null);
                }
            });
        } else {
            window.addEventListener("keydown", event => {
                if (panel.isConnected && event.key === "Escape" && !document.querySelector(".dependency-graph-modal[open]")) {
                    choose(null);
                }
            });
            window.addEventListener("popstate", () => {
                if (panel.isConnected) focusVariable(new URLSearchParams(location.search).get("graph_variable"));
            });
        }
        panel.querySelector('[data-action="zoom-in"]').addEventListener("click", () => setZoom(scale * 1.4));
        panel.querySelector('[data-action="zoom-out"]').addEventListener("click", () => setZoom(scale / 1.4));
        panel.querySelector('[data-action="fit"]').addEventListener("click", fitGraph);
        focusButton.addEventListener("click", focusSelected);
        fitGraph();
        if (!dialog) focusVariable(new URLSearchParams(location.search).get("graph_variable"));
        return { focusVariable };
    } catch (error) {
        viewport.textContent = "The graph could not be loaded. You can download the SVG below.";
        console.error(error);
    }
}

document$.subscribe(() => {
    const panel = document.querySelector("#dependency-graph-viewer");
    if (panel) initializeDependencyGraph(panel, document.querySelector("#dependency-graph-source").href);

    let dialog;
    let graphReady;
    // MathJax creates equation links later, so handle clicks on the page itself.
    const content = document.querySelector(".md-content");
    if (!content) return;
    content.addEventListener("click", async event => {
        const link = event.target.closest('a[href*="#var__"]');
        if (!link || !link.hash.startsWith("#var__")) return;
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        const reference = dependencyGraphPage;
        const variable = decodeURIComponent(link.hash.slice("#var__".length));
        if (!dialog) {
            dialog = document.createElement("dialog");
            dialog.className = "dependency-graph-modal";
            dialog.setAttribute("aria-labelledby", "dependency-graph-modal-title");
            dialog.innerHTML = `
                <header>
                    <h2 id="dependency-graph-modal-title">Variable dependencies</h2>
                    <button type="button" aria-label="Close dependency graph" autofocus>×</button>
                </header>
                <p>Loading dependency graph…</p>`;
            dialog.querySelector("button").addEventListener("click", () => dialog.close());
            document.body.append(dialog);
            // Reuse the reference page's controls and graph, loaded once per page.
            graphReady = (async () => {
                const response = await fetch(reference);
                if (!response.ok) throw new Error(`Reference page request failed: ${response.status}`);
                const page = new DOMParser().parseFromString(await response.text(), "text/html");
                const graphPanel = page.querySelector("#dependency-graph-viewer");
                const source = new URL(page.querySelector("#dependency-graph-source").getAttribute("href"), reference);
                dialog.querySelector("p").replaceWith(graphPanel);
                return initializeDependencyGraph(graphPanel, source, dialog);
            })();
        }
        dialog.showModal();
        try {
            const graph = await graphReady;
            if (dialog.open) graph?.focusVariable(variable);
        } catch (error) {
            dialog.querySelector("p").textContent = "The graph could not be loaded. Please try the variable reference page.";
            console.error(error);
        }
    });
});
