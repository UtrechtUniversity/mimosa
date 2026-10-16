document$.subscribe(() => {
    const panel = document.querySelector("#dependency-demo");
    if (!panel) return;

    // This is deliberately a small, invented graph, independent of MIMOSA.
    const nodes = [
        { id: "demo_heat", x: 110, y: 65 },
        { id: "demo_exposure", x: 110, y: 185 },
        { id: "demo_adaptation", x: 110, y: 305 },
        { id: "demo_damage", x: 360, y: 125 },
        { id: "demo_welfare", x: 610, y: 185 },
    ];
    const edges = [
        ["demo_heat", "demo_damage"],
        ["demo_exposure", "demo_damage"],
        ["demo_adaptation", "demo_damage"],
        ["demo_adaptation", "demo_welfare"],
        ["demo_damage", "demo_welfare"],
    ];
    const svg = panel.querySelector("svg");
    const status = panel.querySelector(".dependency-demo-status");

    function addSvg(parent, tag, attributes) {
        const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
        Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
        parent.append(element);
        return element;
    }

    const definitions = addSvg(svg, "defs", {});
    Object.entries({ normal: "#999", incoming: "#2297d5", outgoing: "#ed6a2f" }).forEach(([kind, color]) => {
        const marker = addSvg(definitions, "marker", {
            id: `demo-arrow-${kind}`, viewBox: "0 0 10 10", refX: 9, refY: 5,
            markerWidth: 7, markerHeight: 7, orient: "auto-start-reverse",
        });
        addSvg(marker, "path", { d: "M 0 0 L 10 5 L 0 10 Z", fill: color });
    });

    const edgeElements = edges.map(([source, target]) => {
        const from = nodes.find(node => node.id === source);
        const to = nodes.find(node => node.id === target);
        return addSvg(svg, "path", {
            class: "demo-edge", "data-source": source, "data-target": target,
            d: `M ${from.x + 85} ${from.y} C ${from.x + 155} ${from.y}, ${to.x - 155} ${to.y}, ${to.x - 85} ${to.y}`,
        });
    });

    const nodeElements = nodes.map(node => {
        const link = addSvg(svg, "a", {
            href: `?demo_variable=${node.id}#dependency-graph-demo`,
            class: "demo-node", "data-variable": node.id,
            "aria-label": `Highlight ${node.id}`,
        });
        addSvg(link, "rect", { x: node.x - 85, y: node.y - 28, width: 170, height: 56, rx: 12 });
        addSvg(link, "text", { x: node.x, y: node.y, "text-anchor": "middle", "dominant-baseline": "middle" }).textContent = node.id;
        link.addEventListener("click", event => {
            event.preventDefault();
            history.pushState(null, "", link.getAttribute("href"));
            highlight(node.id);
        });
        return link;
    });

    function highlight(selected) {
        const incoming = edges.filter(([, target]) => target === selected).map(([source]) => source);
        const outgoing = edges.filter(([source]) => source === selected).map(([, target]) => target);

        nodeElements.forEach(node => {
            const id = node.dataset.variable;
            node.classList.toggle("is-selected", id === selected);
            node.classList.toggle("is-incoming", incoming.includes(id));
            node.classList.toggle("is-outgoing", outgoing.includes(id));
            node.classList.toggle("is-muted", id !== selected && !incoming.includes(id) && !outgoing.includes(id));
            if (id === selected) node.setAttribute("aria-current", "true");
            else node.removeAttribute("aria-current");
        });
        edgeElements.forEach(edge => {
            const kind = edge.dataset.target === selected ? "incoming" : edge.dataset.source === selected ? "outgoing" : "normal";
            edge.setAttribute("class", `demo-edge ${kind}`);
            edge.setAttribute("marker-end", `url(#demo-arrow-${kind})`);
        });
        status.textContent = `${selected} — Depends on: ${incoming.join(", ") || "none"}. Used by: ${outgoing.join(", ") || "none"}.`;
    }

    function selectFromUrl() {
        const requested = new URLSearchParams(location.search).get("demo_variable");
        highlight(nodes.some(node => node.id === requested) ? requested : "demo_damage");
    }

    window.addEventListener("popstate", selectFromUrl);
    selectFromUrl();
});
