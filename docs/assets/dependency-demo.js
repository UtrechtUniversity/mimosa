document$.subscribe(async () => {
    const panel = document.querySelector("#dependency-demo");
    if (!panel) return;

    const viewport = panel.querySelector(".dependency-demo-viewport");
    const status = panel.querySelector(".dependency-demo-status");
    const select = panel.querySelector("select");

    try {
        const response = await fetch(document.querySelector("#dependency-demo-source").href);
        if (!response.ok) throw new Error(`Graph request failed: ${response.status}`);
        const graphDocument = new DOMParser().parseFromString(await response.text(), "image/svg+xml");
        const svg = graphDocument.documentElement;
        svg.setAttribute("role", "group");
        svg.setAttribute("aria-label", "ACCREU sectoral variable dependencies");
        viewport.replaceChildren(svg);

        const nodes = Array.from(svg.querySelectorAll("g.node"));
        const edges = Array.from(svg.querySelectorAll("g.edge"));
        const { width, height } = svg.viewBox.baseVal;
        let scale = 1;
        let selected = "damage_costs";

        nodes.forEach(node => {
            const name = node.querySelector("title").textContent;
            node.dataset.variable = name;
            node.classList.add("demo-node");
            const link = node.querySelector("a");
            link.setAttribute("href", `?demo_variable=${encodeURIComponent(name)}#dependency-graph-demo`);
            link.setAttribute("aria-label", `Highlight ${name}`);
            link.addEventListener("click", event => {
                event.preventDefault();
                history.pushState(null, "", link.getAttribute("href"));
                highlight(name);
            });
        });
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
            select.value = name;
            const incoming = edges.filter(edge => edge.dataset.target === name).map(edge => edge.dataset.source);
            const outgoing = edges.filter(edge => edge.dataset.source === name).map(edge => edge.dataset.target);
            nodes.forEach(node => {
                const id = node.dataset.variable;
                node.classList.toggle("is-selected", id === name);
                node.classList.toggle("is-incoming", incoming.includes(id));
                node.classList.toggle("is-outgoing", outgoing.includes(id));
                node.classList.toggle("is-muted", id !== name && !incoming.includes(id) && !outgoing.includes(id));
                node.querySelector("a").setAttribute("aria-current", id === name ? "true" : "false");
            });
            edges.forEach(edge => {
                const kind = edge.dataset.target === name ? "incoming" : edge.dataset.source === name ? "outgoing" : "normal";
                edge.setAttribute("class", `edge demo-edge ${kind}`);
            });
            status.textContent = `${name} — Depends on: ${incoming.join(", ") || "none"}. Used by: ${outgoing.join(", ") || "none"}. Graph: ${nodes.length} variables, ${edges.length} links.`;
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
            panel.classList.remove("is-overview");
            setZoom(Math.max(scale, 0.85));
            const node = nodes.find(node => node.dataset.variable === selected).getBoundingClientRect();
            const frame = viewport.getBoundingClientRect();
            viewport.scrollLeft += node.left - frame.left + node.width / 2 - viewport.clientWidth / 2;
            viewport.scrollTop += node.top - frame.top + node.height / 2 - viewport.clientHeight / 2;
        }

        function selectFromUrl() {
            const requested = new URLSearchParams(location.search).get("demo_variable");
            const exists = nodes.some(node => node.dataset.variable === requested);
            highlight(exists ? requested : "damage_costs");
            if (exists) focusSelected();
        }

        select.addEventListener("change", () => {
            history.pushState(null, "", `?demo_variable=${encodeURIComponent(select.value)}#dependency-graph-demo`);
            highlight(select.value);
            focusSelected();
        });
        panel.querySelector('[data-action="zoom-in"]').addEventListener("click", () => setZoom(scale * 1.4));
        panel.querySelector('[data-action="zoom-out"]').addEventListener("click", () => setZoom(scale / 1.4));
        panel.querySelector('[data-action="fit"]').addEventListener("click", fitGraph);
        panel.querySelector('[data-action="focus"]').addEventListener("click", focusSelected);
        window.addEventListener("popstate", selectFromUrl);
        fitGraph();
        selectFromUrl();
    } catch (error) {
        viewport.textContent = "The graph could not be loaded. You can download the SVG below.";
        console.error(error);
    }
});
