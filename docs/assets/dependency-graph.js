// Resolve the reference page from this asset, independently of the current page.
const dependencyGraphPage = new URL("../variables/", document.currentScript.src);
const dependencyGraphAssets = new URL("dependency-graphs/", document.currentScript.src);
const dependencyGraphRequests = new Map();

function loadDependencyAsset(url, format = "text") {
    const key = String(url);
    if (!dependencyGraphRequests.has(key)) {
        dependencyGraphRequests.set(key, fetch(url).then(response => {
            if (!response.ok) throw new Error(`Graph request failed: ${response.status}`);
            return response[format]();
        }));
    }
    return dependencyGraphRequests.get(key);
}

function parseDependencyLink(hash, pageContext = "coacch") {
    const parts = decodeURIComponent(hash.slice("#var__".length)).split("::");
    const context = parts.length === 2 ? parts[0] : pageContext;
    return { context: context === "default" ? "coacch" : context, variable: parts.at(-1) };
}

let variableReferencePage;

function loadVariableReference() {
    if (!variableReferencePage) {
        variableReferencePage = loadDependencyAsset(dependencyGraphPage).then(html =>
            new DOMParser().parseFromString(html, "text/html")
        );
    }
    return variableReferencePage;
}

// Graph nodes and documentation links share the same card content and placement.
function createVariableTooltip(container, id) {
    const tooltip = document.createElement("div");
    tooltip.className = "dependency-graph-tooltip md-typeset";
    tooltip.id = id;
    tooltip.setAttribute("role", "tooltip");
    tooltip.tabIndex = -1;
    tooltip.hidden = true;
    container.append(tooltip);
    let activeLink = null;
    let hideTimer;

    function keepOpen() {
        clearTimeout(hideTimer);
    }

    function hide() {
        keepOpen();
        tooltip.hidden = true;
        activeLink?.removeAttribute("aria-describedby");
        activeLink = null;
    }

    function show(target, link, reference, context, variable) {
        hide();
        const anchor = reference.getElementById(`variable-${context}--${variable}`);
        const entry = anchor?.closest(".admonition.variable");
        if (!entry) return;
        const card = entry.cloneNode(true);
        card.querySelectorAll(".variable_anchor, .md-clipboard").forEach(element => element.remove());
        card.querySelectorAll("[id]").forEach(element => element.removeAttribute("id"));
        tooltip.replaceChildren(card);
        tooltip.hidden = false;
        activeLink = link;
        link.setAttribute("aria-describedby", tooltip.id);

        const bounds = container.closest("dialog")?.getBoundingClientRect() || {
            left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight,
        };
        const rect = target.getBoundingClientRect();
        const width = tooltip.offsetWidth;
        const height = tooltip.offsetHeight;
        let left = rect.right + width + 12 < bounds.right ? rect.right + 8 : rect.left - width - 8;
        let top = rect.top;
        if (left < bounds.left + 8) {
            // When neither side has room, place the card above or below the target.
            left = rect.left;
            top = rect.top - height - 8;
            if (top < bounds.top + 8) top = rect.bottom + 8;
        }
        tooltip.style.left = `${Math.max(bounds.left + 8, Math.min(left, bounds.right - width - 8))}px`;
        tooltip.style.top = `${Math.max(bounds.top + 8, Math.min(top, bounds.bottom - height - 8))}px`;
    }

    function scheduleHide() {
        keepOpen();
        hideTimer = setTimeout(hide, 150);
    }
    tooltip.addEventListener("pointerenter", keepOpen);
    tooltip.addEventListener("pointerleave", scheduleHide);
    tooltip.addEventListener("focusin", keepOpen);
    tooltip.addEventListener("focusout", scheduleHide);
    return {
        hide, show, keepOpen, scheduleHide,
        contains: target => tooltip.contains(target),
        destroy() { hide(); tooltip.remove(); },
    };
}

function initializeDependencyTooltips(panel, nodes, reference, signal) {
    const id = panel.closest("dialog") ? "dependency-graph-modal-tooltip" : "dependency-graph-tooltip";
    const tooltip = createVariableTooltip(panel, id);
    let showTimer;

    function hide() {
        clearTimeout(showTimer);
        tooltip.hide();
    }
    function show(node) {
        clearTimeout(showTimer);
        tooltip.show(node, node.querySelector("a"), reference, panel.dataset.variableContext, node.dataset.variable);
    }
    function scheduleHide() {
        clearTimeout(showTimer);
        tooltip.scheduleHide();
    }
    nodes.forEach(node => {
        // Replace Graphviz's native name-only tooltip with the reference entry.
        node.querySelector("title").remove();
        const link = node.querySelector("a");
        link.removeAttributeNS("http://www.w3.org/1999/xlink", "title");
        node.addEventListener("pointerenter", () => {
            clearTimeout(showTimer);
            tooltip.keepOpen();
            showTimer = setTimeout(() => show(node), 250);
        });
        node.addEventListener("pointerleave", scheduleHide);
        link.addEventListener("focus", () => requestAnimationFrame(() => {
            // Let the browser scroll a keyboard-focused node into view first.
            if (document.activeElement === link) show(node);
        }));
        link.addEventListener("blur", scheduleHide);
    });
    panel.querySelector(".dependency-graph-viewport").addEventListener("scroll", hide);
    panel.closest("dialog")?.addEventListener("close", hide, { signal });
    return { hide };
}

function initializeVariableLinkTooltips(content, pageContext) {
    const tooltip = createVariableTooltip(content, "variable-link-tooltip");
    const events = new AbortController();
    const options = { signal: events.signal };
    const localReference = content.querySelector("#dependency-graph-viewer") ? document : null;
    let showTimer;
    let requestId = 0;

    function hide() {
        clearTimeout(showTimer);
        requestId++;
        tooltip.hide();
    }
    function schedule(link, delay = 250) {
        hide();
        const request = requestId;
        showTimer = setTimeout(async () => {
            try {
                const reference = localReference || await loadVariableReference();
                if (request !== requestId || !link.isConnected) return;
                const { context, variable } = parseDependencyLink(link.hash, pageContext);
                tooltip.show(link, link, reference, context, variable);
            } catch (error) {
                console.error(error);
            }
        }, delay);
    }
    function variableLink(event) {
        const link = event.target.closest('a[href*="#var__"]');
        if (!link?.hash.startsWith("#var__") || link.contains(event.relatedTarget)) return null;
        return link;
    }
    function leave(event) {
        if (!variableLink(event)) return;
        clearTimeout(showTimer);
        requestId++;
        if (tooltip.contains(event.relatedTarget)) tooltip.keepOpen();
        else tooltip.scheduleHide();
    }
    // Delegation also covers equation anchors added later by MathJax.
    content.addEventListener("pointerover", event => {
        const link = variableLink(event);
        if (link && event.pointerType !== "touch") schedule(link);
    }, options);
    content.addEventListener("pointerout", leave, options);
    content.addEventListener("focusin", event => {
        const link = variableLink(event);
        if (link) requestAnimationFrame(() => {
            if (document.activeElement === link && content.isConnected) schedule(link, 0);
        });
    }, options);
    content.addEventListener("focusout", leave, options);
    content.addEventListener("click", event => {
        if (!tooltip.contains(event.target)) hide();
    }, options);
    window.addEventListener("keydown", event => {
        if (event.key === "Escape") hide();
    }, options);
    window.addEventListener("scroll", event => {
        if (!tooltip.contains(event.target)) hide();
    }, { ...options, capture: true, passive: true });
    window.addEventListener("resize", hide, options);
    return { destroy() { hide(); events.abort(); tooltip.destroy(); } };
}

async function initializeDependencyGraph(panel, source, dialog = null, reference = document) {
    const viewport = panel.querySelector(".dependency-graph-viewport");
    const select = panel.querySelector("select");
    const focusButton = panel.querySelector('[data-action="focus"]');

    const events = new AbortController();
    try {
        const graphDocument = new DOMParser().parseFromString(await loadDependencyAsset(source), "image/svg+xml");
        const svg = graphDocument.documentElement;
        svg.setAttribute("role", "group");
        svg.setAttribute("aria-label", "Model variable dependencies");
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
            const url = new URL(dependencyGraphPage);
            url.searchParams.set("graph_context", panel.dataset.variableContext);
            url.searchParams.set("graph_variable", name);
            url.hash = "dependency-graph";
            link.setAttribute("href", url.href);
            link.setAttribute("aria-label", `Highlight ${name}`);
            link.addEventListener("click", event => {
                event.preventDefault();
                choose(name);
                if (scale < focusZoom) focusSelected();
            });
        });
        const tooltips = initializeDependencyTooltips(panel, nodes, reference, events.signal);
        const hideTooltip = tooltips.hide;
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
            hideTooltip();
            if (!dialog) {
                const url = new URL(location.href);
                if (name) url.searchParams.set("graph_variable", name);
                else url.searchParams.delete("graph_variable");
                url.searchParams.set("graph_context", panel.dataset.variableContext);
                url.hash = "dependency-graph";
                history.replaceState(history.state, "", url);
            }
            highlight(name);
            if (!name && document.activeElement?.closest(".dependency-node")) {
                document.activeElement.blur();
            }
        }

        function setZoom(next) {
            hideTooltip();
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
            hideTooltip();
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
            hideTooltip();
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
            }, { signal: events.signal });
        } else {
            window.addEventListener("keydown", event => {
                if (panel.isConnected && event.key === "Escape" && !document.querySelector(".dependency-graph-modal[open]")) {
                    choose(null);
                }
            }, { signal: events.signal });
        }
        panel.querySelector('[data-action="zoom-in"]').addEventListener("click", () => setZoom(scale * 1.4));
        panel.querySelector('[data-action="zoom-out"]').addEventListener("click", () => setZoom(scale / 1.4));
        panel.querySelector('[data-action="fit"]').addEventListener("click", fitGraph);
        focusButton.addEventListener("click", focusSelected);
        fitGraph();
        return {
            focusVariable,
            destroy() { events.abort(); hideTooltip(); },
        };
    } catch (error) {
        viewport.textContent = "The graph could not be loaded. You can download the SVG below.";
        console.error(error);
    }
}

async function createDependencyGraphController(panel, reference, dialog = null, downloadLink = null) {
    const manifest = await loadDependencyAsset(new URL("index.json", dependencyGraphAssets), "json");
    const template = panel.cloneNode(true);
    let viewer;
    let activeContext;
    let requestId = 0;

    async function open(context, variable = null) {
        context = context === "default" ? "coacch" : context || manifest.default_context;
        const request = ++requestId;
        const config = manifest.contexts[context];
        if (context !== activeContext || !viewer) {
            viewer?.destroy();
            viewer = null;
            const nextPanel = template.cloneNode(true);
            panel.replaceWith(nextPanel);
            panel = nextPanel;
            panel.dataset.variableContext = context;
            activeContext = context;
            const configuration = panel.querySelector(".dependency-graph-configuration");
            // This HTML is generated locally from configuration parameters at build time.
            if (config) configuration.innerHTML = config.configuration_html;
            else configuration.textContent = `Unknown configuration: ${context}`;
            if (config) {
                const source = new URL(config.source, dependencyGraphAssets);
                if (downloadLink) downloadLink.href = source.href;
                const nextViewer = await initializeDependencyGraph(panel, source, dialog, reference);
                if (request !== requestId) { nextViewer?.destroy(); return; }
                viewer = nextViewer;
            } else {
                panel.querySelector(".dependency-graph-viewport").textContent = "This model configuration has no documented graph.";
            }
        }
        if (request !== requestId) return;
        viewer?.focusVariable(variable);
        if (!dialog && config?.variables.includes(variable)) {
            const url = new URL(location.href);
            url.searchParams.set("graph_context", context);
            url.searchParams.set("graph_variable", variable);
            url.hash = "dependency-graph";
            history.replaceState(history.state, "", url);
        }
        const message = panel.querySelector(".dependency-graph-message");
        message.replaceChildren();
        message.hidden = !variable || !!config?.variables.includes(variable);
        if (!message.hidden) {
            const text = document.createElement("p");
            text.textContent = `${variable} is unavailable in this configuration.`;
            message.append(text);
            const alternatives = Object.entries(manifest.contexts).filter(([, entry]) => entry.variables.includes(variable));
            if (alternatives.length) {
                const select = document.createElement("select");
                select.setAttribute("aria-label", "Available model configurations");
                alternatives.forEach(([name, entry]) => select.add(new Option(entry.label, name)));
                const button = document.createElement("button");
                button.type = "button";
                button.textContent = "Open available configuration";
                button.addEventListener("click", () => open(select.value, variable));
                message.append(select, button);
            } else {
                text.textContent += " No documented graph contains this variable.";
            }
        }
    }
    return { open };
}

let variableLinkTooltips;

document$.subscribe(() => {
    variableLinkTooltips?.destroy();
    const pageContext = document.querySelector("[data-documentation-context]")?.dataset.documentationContext || "coacch";
    const panel = document.querySelector("#dependency-graph-viewer");
    if (panel) {
        const controller = createDependencyGraphController(panel, document, null, document.querySelector("#dependency-graph-source"));
        function selectFromUrl() {
            const query = new URLSearchParams(location.search);
            controller.then(graph => graph.open(query.get("graph_context") || pageContext, query.get("graph_variable")));
        }
        selectFromUrl();
        window.addEventListener("popstate", selectFromUrl);
    }

    let dialog;
    let graphReady;
    // MathJax creates equation links later, so handle clicks on the page itself.
    const content = document.querySelector(".md-content");
    if (!content) return;
    variableLinkTooltips = initializeVariableLinkTooltips(content, pageContext);
    async function openVariable(hash) {
        const { context, variable } = parseDependencyLink(hash, pageContext);
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
            graphReady = (async () => {
                const page = await loadVariableReference();
                const graphPanel = page.querySelector("#dependency-graph-viewer").cloneNode(true);
                dialog.querySelector("p").replaceWith(graphPanel);
                return createDependencyGraphController(graphPanel, page, dialog);
            })();
        }
        dialog.showModal();
        try {
            const graph = await graphReady;
            if (dialog.open) await graph.open(context, variable);
        } catch (error) {
            console.error(error);
            const message = dialog.querySelector(".dependency-graph-viewport, p");
            if (message) message.textContent = "The graph could not be loaded. Please try the variable reference page.";
        }
    }
    content.addEventListener("click", event => {
        const link = event.target.closest('a[href*="#var__"]');
        if (!link || !link.hash.startsWith("#var__")) return;
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        openVariable(link.hash);
    });
    function openFromHash() {
        if (content.isConnected && location.hash.startsWith("#var__")) openVariable(location.hash);
    }
    openFromHash();
    window.addEventListener("hashchange", openFromHash);
});
